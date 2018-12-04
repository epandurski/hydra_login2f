# How to run the example:

1. Install `docker` and `docker-compose`.

2. Change the current directory to `example/`.

3. Run `docker-compose up`. The first time you run it, it may take
   some time to initialize the database schema.

4. Open a browser window on this
   [location](http://localhost:4444/oauth2/auth?client_id=consumer-app&redirect_uri=http://localhost:4488/users/hello_world&response_type=code&state=1234567890&scope=openid).

5. To read the mock email messages that the example deployment sends,
   open a browser window [here](http://localhost:8025/).
