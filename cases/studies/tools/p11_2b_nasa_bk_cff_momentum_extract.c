#define main p11_2b_nasa_bk_cff_base_main
#include "p11_2b_nasa_bk_cff_extract.c"
#undef main

/*
 * Companion extractor for the axial momentum-flux quantity required by the
 * reduced-order NASA-BK closure.  Reuse of the already-reviewed low-level CFF
 * helpers keeps the ADF compatibility and Wind-US VSCLST/REFARR scaling rules
 * identical to the thermal extraction.
 */
int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s GRID_COMPAT FLOW_COMPAT OUTPUT_CSV\n", argv[0]);
        return 2;
    }

    int cgd = 0, cfl = 0;
    fail_cgio(cgio_open_file(argv[1], CGIO_MODE_READ, CGIO_FILE_ADF, &cgd), "open grid CFF");
    fail_cgio(cgio_open_file(argv[2], CGIO_MODE_READ, CGIO_FILE_ADF, &cfl), "open flow CFF");
    double grid_root = 0.0, flow_root = 0.0;
    fail_cgio(cgio_get_root_id(cgd, &grid_root), "grid root");
    fail_cgio(cgio_get_root_id(cfl, &flow_root), "flow root");
    ScaleTable grid_scales = load_scales(cgd, grid_root);
    ScaleTable flow_scales = load_scales(cfl, flow_root);

    const ScaleEntry *sx = find_scale(&grid_scales, "x");
    const ScaleEntry *sy = find_scale(&grid_scales, "y");
    const ScaleEntry *srho = find_scale(&flow_scales, "rho");
    const ScaleEntry *srhou = find_scale(&flow_scales, "rho*u");
    const ScaleEntry *sp = find_scale(&flow_scales, "p");

    FILE *out = fopen(argv[3], "w");
    if (!out) {
        fprintf(stderr, "cannot open output '%s': %s\n", argv[3], strerror(errno));
        return 2;
    }
    fprintf(out, "zone,i_index,x_mid_m,x_span_m,height_m,mass_flux_per_width_kg_m_s,momentum_flux_per_width_N_per_m,area_weighted_p_Pa\n");

    int selected_zones = 0;
    for (int zone_number = 1; zone_number <= MAX_ZONES; ++zone_number) {
        char zone_name[33];
        snprintf(zone_name, sizeof(zone_name), "ZONE%4d", zone_number);
        double gz = 0.0, fz = 0.0;
        if (cgio_get_node_id(cgd, grid_root, zone_name, &gz) != 0) break;
        fail_cgio(cgio_get_node_id(cfl, flow_root, zone_name, &fz), "matching flow zone");

        int ni = 0, nj = 0, fni = 0, fnj = 0;
        int n = read_zone_dims(cgd, gz, &ni, &nj);
        int fn = read_zone_dims(cfl, fz, &fni, &fnj);
        if (n != fn || ni != fni || nj != fnj) fail_msg("grid/flow zone dimension mismatch");

        double *x_raw = read_r8(cgd, gz, "x", n);
        double *y_raw = read_r8(cgd, gz, "y", n);
        double xmin = INFINITY, xmax = -INFINITY;
        for (int k = 0; k < n; ++k) {
            double x = dimensionalize(x_raw[k], sx);
            if (x < xmin) xmin = x;
            if (x > xmax) xmax = x;
        }

        const double tol = 5.0e-5;
        int is_main = (xmin >= -tol && xmax > tol && xmax <= 0.356 + tol && nj == 145);
        if (!is_main) {
            free(x_raw);
            free(y_raw);
            continue;
        }
        ++selected_zones;

        float *rho_raw = read_r4(cfl, fz, "rho", n);
        float *rhou_raw = read_r4(cfl, fz, "rho*u", n);
        float *p_raw = read_r4(cfl, fz, "p", n);

        for (int i = 0; i < ni; ++i) {
            double xlo = INFINITY, xhi = -INFINITY, xsum = 0.0;
            double ymin = INFINITY, ymax = -INFINITY;
            double mdot_w = 0.0, momentum_w = 0.0, p_area_w = 0.0;

            double *yv = (double *)malloc((size_t)nj * sizeof(double));
            double *rhouv = (double *)malloc((size_t)nj * sizeof(double));
            double *momentumv = (double *)malloc((size_t)nj * sizeof(double));
            double *pv = (double *)malloc((size_t)nj * sizeof(double));
            if (!yv || !rhouv || !momentumv || !pv) fail_msg("allocation failure");

            for (int j = 0; j < nj; ++j) {
                int k = j * ni + i;
                double x = dimensionalize(x_raw[k], sx);
                double y = dimensionalize(y_raw[k], sy);
                double rho = dimensionalize(rho_raw[k], srho);
                double rhou = dimensionalize(rhou_raw[k], srhou);
                double pressure = dimensionalize(p_raw[k], sp);
                if (!(rho > 0.0) || !(pressure > 0.0) || !isfinite(rhou)) {
                    fail_msg("nonphysical dimensionalized NASA reference momentum state");
                }
                double u = rhou / rho;
                yv[j] = y;
                rhouv[j] = rhou;
                momentumv[j] = rhou * u + pressure;
                pv[j] = pressure;
                if (x < xlo) xlo = x;
                if (x > xhi) xhi = x;
                xsum += x;
                if (y < ymin) ymin = y;
                if (y > ymax) ymax = y;
            }

            for (int j = 0; j < nj - 1; ++j) {
                mdot_w += trapz_pair(rhouv[j], rhouv[j + 1], yv[j], yv[j + 1]);
                momentum_w += trapz_pair(momentumv[j], momentumv[j + 1], yv[j], yv[j + 1]);
                p_area_w += trapz_pair(pv[j], pv[j + 1], yv[j], yv[j + 1]);
            }
            double height = ymax - ymin;
            if (!(mdot_w > 0.0) || !(height > 0.0) || !(momentum_w > 0.0)) {
                fail_msg("invalid main-duct integrated momentum section");
            }
            fprintf(out, "%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
                    zone_number, i, xsum / (double)nj, xhi - xlo, height,
                    mdot_w, momentum_w, p_area_w / height);

            free(yv);
            free(rhouv);
            free(momentumv);
            free(pv);
        }

        free(x_raw);
        free(y_raw);
        free(rho_raw);
        free(rhou_raw);
        free(p_raw);
    }

    fclose(out);
    cgio_close_file(cgd);
    cgio_close_file(cfl);
    if (selected_zones != 7) {
        fprintf(stderr, "expected 7 source-backed main-duct zones, found %d\n", selected_zones);
        return 2;
    }
    return 0;
}
