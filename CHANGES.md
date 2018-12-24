Changelog
=========


Version 0.9.5
-----------

- Fixed a potential security issue caused by storing potentially
  sensitive data in Redis. Now only cryptographic hashes are stored
  instead of the data.

- Improved README


Version 0.9.4
-----------

- Added database connection pooling configuration settings
- Improved default logging configuration
- Improved Dockerfile


Version 0.9.3
-----------

- Do not require verification code after password change
- Use python:3.7-alpine for the docker image


Version 0.9.2
-----------

- Added `SUBJECT_PREFIX` parameter
- Minor improvement in the `example/`


Version 0.9.1
-----------

- Fixed bug in MySQL support



Version 0.9
-----------

- Initial public release
