# -*- coding: utf-8 -*-
from trendlines.app_factory import create_app

PORT = 5001

app = create_app()
app.run(debug=True, port=PORT, use_reloader=True)
