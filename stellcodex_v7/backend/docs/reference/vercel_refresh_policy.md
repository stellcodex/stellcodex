# Vercel Refresh Policy

STELLCODEX should keep public pages fresh on Vercel without turning every
request into server work.

Policy:

- public route group uses interval-based revalidation
- default public interval: 1800 seconds
- faster public status interval: 300 seconds
- community feed interval: 900 seconds
- workspace and app routes stay request-driven through client-side data and
  canonical redirects instead of broad forced revalidation

Rules:

- prefer route-segment revalidation over request-time rendering for public copy
- keep refresh intervals explicit in code
- do not add duplicate marketing or dashboard pages to work around cache issues
- keep STELLCODEX suite copy aligned across public pages
