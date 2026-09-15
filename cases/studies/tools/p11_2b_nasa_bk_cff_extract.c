#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cgns_io.h"

#define MAX_SCALE_VARS 512
#define CFF_NAME_LEN 32
#define MAX_ZONES 64

typedef struct {
    char name[CFF_NAME_LEN + 1];
    double so, sf, ro, rf;
} ScaleEntry;

typedef struct {
    ScaleEntry entries[MAX_SCALE_VARS];
    int count;
} ScaleTable;

static void fail_cgio(int ierr, const char *where) {
    if (!ierr) return;
    char msg[256] = {0};
    cgio_error_message(msg);
    fprintf(stderr, "%s: %s\n", where, msg);
    exit(2);
}

static void fail_msg(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(2);
}

static double child_id(int cgio, double parent, const char *name) {
    double id = 0.0;
    int ierr = cgio_get_node_id(cgio, parent, name, &id);
    if (ierr) {
        char msg[256] = {0};
        cgio_error_message(msg);
        fprintf(stderr, "missing CFF node '%s': %s\n", name, msg);
        exit(2);
    }
    return id;
}

static void trim_name(char *text) {
    for (int i = CFF_NAME_LEN - 1; i >= 0; --i) {
        if (text[i] == ' ' || text[i] == '\0') text[i] = '\0';
        else break;
    }
}

static ScaleTable load_scales(int cgio, double root) {
    ScaleTable table;
    memset(&table, 0, sizeof(table));
    double ref = child_id(cgio, root, "RefScl00000001_CFF");
    double vs_id = child_id(cgio, ref, "VSCLST");
    double arr_id = child_id(cgio, ref, "REFARR");

    char names[MAX_SCALE_VARS * CFF_NAME_LEN];
    float values[MAX_SCALE_VARS * 4];
    memset(names, 0, sizeof(names));
    memset(values, 0, sizeof(values));
    fail_cgio(cgio_read_all_data(cgio, vs_id, names), "read VSCLST");
    fail_cgio(cgio_read_all_data(cgio, arr_id, values), "read REFARR");

    for (int i = 0; i < MAX_SCALE_VARS; ++i) {
        char name[CFF_NAME_LEN + 1];
        memcpy(name, names + i * CFF_NAME_LEN, CFF_NAME_LEN);
        name[CFF_NAME_LEN] = '\0';
        trim_name(name);
        if (!name[0]) continue;
        if (table.count >= MAX_SCALE_VARS) fail_msg("too many CFF scaling entries");
        ScaleEntry *entry = &table.entries[table.count++];
        snprintf(entry->name, sizeof(entry->name), "%s", name);
        entry->so = values[4 * i + 0];
        entry->sf = values[4 * i + 1];
        entry->ro = values[4 * i + 2];
        entry->rf = values[4 * i + 3];
    }
    return table;
}

static const ScaleEntry *find_scale(const ScaleTable *table, const char *name) {
    for (int i = 0; i < table->count; ++i) {
        if (strcmp(table->entries[i].name, name) == 0) return &table->entries[i];
    }
    fprintf(stderr, "CFF scaling entry not found for '%s'\n", name);
    exit(2);
}

static double dimensionalize(double stored, const ScaleEntry *scale) {
    /* Wind-US Common File scaling convention:
       V_dimensional = V_file * RF + RO
       V_SI = V_dimensional * SF + SO. */
    return (stored * scale->rf + scale->ro) * scale->sf + scale->so;
}

static int read_zone_dims(int cgio, double zone, int *ni, int *nj) {
    double id = child_id(cgio, zone, "idat_cff");
    int values[64];
    memset(values, 0, sizeof(values));
    fail_cgio(cgio_read_all_data(cgio, id, values), "read zone idat_cff");
    if (values[0] < 2 || values[1] < 2 || values[2] != 1) {
        fprintf(stderr, "unsupported CFF zone dimensions: %d x %d x %d\n", values[0], values[1], values[2]);
        exit(2);
    }
    *ni = values[0];
    *nj = values[1];
    return values[0] * values[1];
}

static double *read_r8(int cgio, double parent, const char *name, int n) {
    double id = child_id(cgio, parent, name);
    char dtype[3] = {0};
    cglong_t bytes = 0;
    fail_cgio(cgio_get_data_type(cgio, id, dtype), "get R8 type");
    fail_cgio(cgio_get_data_size(cgio, id, &bytes), "get R8 size");
    if (strcmp(dtype, "R8") != 0 || bytes != (cglong_t)(n * (int)sizeof(double))) {
        fprintf(stderr, "node '%s' expected R8[%d], got %s and %lld bytes\n", name, n, dtype, (long long)bytes);
        exit(2);
    }
    double *data = (double *)malloc((size_t)n * sizeof(double));
    if (!data) fail_msg("allocation failure");
    fail_cgio(cgio_read_all_data(cgio, id, data), "read R8 node");
    return data;
}

static float *read_r4(int cgio, double parent, const char *name, int n) {
    double id = child_id(cgio, parent, name);
    char dtype[3] = {0};
    cglong_t bytes = 0;
    fail_cgio(cgio_get_data_type(cgio, id, dtype), "get R4 type");
    fail_cgio(cgio_get_data_size(cgio, id, &bytes), "get R4 size");
    if (strcmp(dtype, "R4") != 0 || bytes != (cglong_t)(n * (int)sizeof(float))) {
        fprintf(stderr, "node '%s' expected R4[%d], got %s and %lld bytes\n", name, n, dtype, (long long)bytes);
        exit(2);
    }
    float *data = (float *)malloc((size_t)n * sizeof(float));
    if (!data) fail_msg("allocation failure");
    fail_cgio(cgio_read_all_data(cgio, id, data), "read R4 node");
    return data;
}

static double trapz_pair(double f0, double f1, double y0, double y1) {
    double dy = y1 - y0;
    if (!(dy > 0.0) || !isfinite(dy)) fail_msg("main-duct transverse coordinate is not strictly increasing");
    return 0.5 * (f0 + f1) * dy;
}

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
    const ScaleEntry *srhov = find_scale(&flow_scales, "rho*v");
    const ScaleEntry *sT = find_scale(&flow_scales, "T");
    const ScaleEntry *sa = find_scale(&flow_scales, "a");
    const ScaleEntry *sp = find_scale(&flow_scales, "p");
    const ScaleEntry *sgamma = find_scale(&flow_scales, "gamma");

    FILE *out = fopen(argv[3], "w");
    if (!out) {
        fprintf(stderr, "cannot open output '%s': %s\n", argv[3], strerror(errno));
        return 2;
    }
    fprintf(out, "zone,i_index,x_mid_m,x_span_m,y_min_m,y_max_m,height_m,mass_flux_per_width_kg_m_s,thermal_T_flux_per_width_kgK_m_s,kinetic_energy_flux_per_width_W_m,mass_flux_weighted_T_K,mass_flux_weighted_Mach,area_weighted_p_Pa,area_weighted_gamma\n");

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

        /* Source-backed main combustor topology: downstream of injection x=0,
           ending at the 0.356 m measurement plane, and spanning the full duct
           height with the common 145-point transverse grid. */
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
        float *rhov_raw = read_r4(cfl, fz, "rho*v", n);
        float *T_raw = read_r4(cfl, fz, "T", n);
        float *a_raw = read_r4(cfl, fz, "a", n);
        float *p_raw = read_r4(cfl, fz, "p", n);
        float *gamma_raw = read_r4(cfl, fz, "gamma", n);

        for (int i = 0; i < ni; ++i) {
            double xlo = INFINITY, xhi = -INFINITY, xsum = 0.0;
            double ymin = INFINITY, ymax = -INFINITY;
            double mdot_w = 0.0, thermal_w = 0.0, kinetic_w = 0.0;
            double mach_flux_w = 0.0, p_area_w = 0.0, gamma_area_w = 0.0;

            double *yv = (double *)malloc((size_t)nj * sizeof(double));
            double *rhouv = (double *)malloc((size_t)nj * sizeof(double));
            double *Tv = (double *)malloc((size_t)nj * sizeof(double));
            double *kinv = (double *)malloc((size_t)nj * sizeof(double));
            double *machv = (double *)malloc((size_t)nj * sizeof(double));
            double *pv = (double *)malloc((size_t)nj * sizeof(double));
            double *gv = (double *)malloc((size_t)nj * sizeof(double));
            if (!yv || !rhouv || !Tv || !kinv || !machv || !pv || !gv) fail_msg("allocation failure");

            for (int j = 0; j < nj; ++j) {
                int k = j * ni + i;
                double x = dimensionalize(x_raw[k], sx);
                double y = dimensionalize(y_raw[k], sy);
                double rho = dimensionalize(rho_raw[k], srho);
                double rhou = dimensionalize(rhou_raw[k], srhou);
                double rhov = dimensionalize(rhov_raw[k], srhov);
                double temp = dimensionalize(T_raw[k], sT);
                double sound = dimensionalize(a_raw[k], sa);
                double pressure = dimensionalize(p_raw[k], sp);
                double gamma = dimensionalize(gamma_raw[k], sgamma);
                if (!(rho > 0.0) || !(sound > 0.0) || !(temp > 0.0) || !isfinite(rhou) || !isfinite(rhov)) {
                    fail_msg("nonphysical dimensionalized NASA reference state");
                }
                double u = rhou / rho;
                double v = rhov / rho;
                double speed2 = u * u + v * v;
                yv[j] = y;
                rhouv[j] = rhou;
                Tv[j] = temp;
                kinv[j] = rhou * 0.5 * speed2;
                machv[j] = rhou * sqrt(speed2) / sound;
                pv[j] = pressure;
                gv[j] = gamma;
                if (x < xlo) xlo = x;
                if (x > xhi) xhi = x;
                xsum += x;
                if (y < ymin) ymin = y;
                if (y > ymax) ymax = y;
            }

            for (int j = 0; j < nj - 1; ++j) {
                mdot_w += trapz_pair(rhouv[j], rhouv[j + 1], yv[j], yv[j + 1]);
                thermal_w += trapz_pair(rhouv[j] * Tv[j], rhouv[j + 1] * Tv[j + 1], yv[j], yv[j + 1]);
                kinetic_w += trapz_pair(kinv[j], kinv[j + 1], yv[j], yv[j + 1]);
                mach_flux_w += trapz_pair(machv[j], machv[j + 1], yv[j], yv[j + 1]);
                p_area_w += trapz_pair(pv[j], pv[j + 1], yv[j], yv[j + 1]);
                gamma_area_w += trapz_pair(gv[j], gv[j + 1], yv[j], yv[j + 1]);
            }
            double height = ymax - ymin;
            if (!(mdot_w > 0.0) || !(height > 0.0)) fail_msg("invalid main-duct integrated section");
            fprintf(out, "%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
                    zone_number, i, xsum / (double)nj, xhi - xlo, ymin, ymax, height,
                    mdot_w, thermal_w, kinetic_w, thermal_w / mdot_w,
                    mach_flux_w / mdot_w, p_area_w / height, gamma_area_w / height);
            free(yv);
            free(rhouv);
            free(Tv);
            free(kinv);
            free(machv);
            free(pv);
            free(gv);
        }
        free(x_raw);
        free(y_raw);
        free(rho_raw);
        free(rhou_raw);
        free(rhov_raw);
        free(T_raw);
        free(a_raw);
        free(p_raw);
        free(gamma_raw);
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
