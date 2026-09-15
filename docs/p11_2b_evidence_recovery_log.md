# P11.2B Evidence-Recovery Log

## 2026-09-15 public-access check

This log records a bounded, reproducible public-source recovery attempt for
the Jin–Liu model-B formal-case evidence chain. It records access results and
does not convert search snippets, figure pixels, or inferred values into
formal inputs.

### Sources checked

- Jin et al. (2026), *Experimental study on heat release distribution during
  supersonic combustion*, *Combustion and Flame* 287, 114876, DOI
  `10.1016/j.combustflame.2026.114876`.
- Liu et al. (2019), *Dual-Mode Operation and Transition in Axisymmetric
  Scramjets*, *AIAA Journal* 57(11), 4764–4777, DOI `10.2514/1.J058391`.

### What was recovered

- The publisher-indexed Jin record identifies the article, DOI, authors,
  publication date, and abstract.
- Public indexing of the author-posted article text explicitly refers readers
  to “Supplementary Materials” for validation of the one-dimensional model.
- The University of Illinois publication record independently confirms the
  Liu article identity, DOI, journal pages, and its experimental/model-B
  context.

These findings establish that a supplementary-data route may exist. They do
not provide a file name, a downloadable payload, or any of the required
same-condition numerical values.

### Access boundary

On 2026-09-15, automated retrieval of the Jin ScienceDirect full-text page
returned publisher access denial (HTTP 403). No publisher PDF, supplementary
file, repository dataset, CSV, XLSX, MAT, TXT, or author dataset was
downloaded. Consequently no checksum, local raw-data path, digitization, or
derived numerical record is added to the repository in this round.

The accessible Liu primary text continues to support the existing model-B
`phi=1.03` same-row values and the derived `pt3` constraint only. It does not
resolve the Jin `phi=1.04` identity, complete station-3 state, Jin Fig. 14
numerical `Cf`, or a same-condition absolute heat-release chain.

### Formal-case result

`artifacts/p11_2b/p11_2b_readiness.json` remains authoritative:

```text
formal_case_ready = false
```

No value has been promoted, no gate rule has been relaxed, and no P11.2B
heated solver case has been run.

## MANUAL ACTION REQUIRED

Please use an account/browser with legitimate ScienceDirect access to obtain
the original supplementary payload associated with:

```text
Kaiyan Jin et al. (2026)
Experimental study on heat release distribution during supersonic combustion
Combustion and Flame 287, 114876
DOI: 10.1016/j.combustflame.2026.114876
```

Download every file offered under **Supplementary Material(s)**, especially
PDF, ZIP, CSV, XLSX, MAT, TXT, data tables, and original Fig. 14/PLIF assets.
Use original files rather than screenshots. Put the unmodified files in:

```text
references/raw/jin_2026/
```

Do not commit publisher PDFs or copyrighted supplementary files until their
redistribution terms are checked. Once the files are present, the next step is
to create a metadata manifest (file name, SHA-256, source URL, access date,
copyright status), parse only machine-readable data where available, and keep
any figure digitization explicitly `FIGURE_DIGITIZED_EXPLORATORY`.

The required evidence targets remain:

1. an explicit source link resolving model B `phi=1.04` versus Liu model-B
   `phi=1.03`;
2. Fig. 14 `x_i`, `x_m`, `x_c`, `k` plus coordinate convention, or absolute
   tabulated `Qdot'(x)`;
3. the matching total heat power, or matching `delta_ht` and measured `mdot`;
4. the complete station-3 boundary state; and
5. the numerical Jin Fig. 14 `Cf` (or a direct statement that it was
   neglected).
