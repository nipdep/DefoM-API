from defom.factory import create_api

import os
import configparser

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

# if __name__ == '__main__':
app = create_api()
app.config['DEBUG'] = True
app.config['DB_URI'] = config['PROD']['DB_URI']
app.config['NS'] = config['PROD']['NS']
app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']

app.run()