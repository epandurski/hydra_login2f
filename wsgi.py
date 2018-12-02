#!/usr/bin/env python

#######################################################################
# Change the following lines to import/create your flask application! #
#######################################################################
from hydra_login2f import create_app

app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config.get('PORT', 8000), debug=True, use_reloader=False)
