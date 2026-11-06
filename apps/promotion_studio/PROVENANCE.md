# Promotion Studio Provenance and License Notice

Promotion Studio is the M12 local application, extended with scheduler
reliability and a text-only Bluesky adapter for this research preview.

## Source and licensing

- The delivered M12 source did not contain a separate `LICENSE` or `NOTICE`
  file.
- This preview includes the application as an independent component and
  applies the repository owner's MIT license (see `LICENSE` in this directory).
- No third-party source code, social-platform SDK, Postiz/AGPL code, or
  third-party assets are bundled. Runtime code uses the Python standard
  library only.
- If the owner intends a different license for the application, change this
  notice and the component license before redistributing it separately.

## Data and credentials

- No real `local-data`, browser profile, App Password, OAuth/JWT token, cookie,
  private key, or user content is included.
- Tests use fake credentials and local simulated endpoints only.
- Bluesky defaults to dry-run. Live publishing requires explicit environment
  authorization and `publish_authorized: true`.

## Relationship to VeriArbor

Promotion Studio is standalone. It does not import `veriarbor` and does not
require the private host repository. It is included in the same repository for
convenience, not because the VeriArbor library drives the GUI.
