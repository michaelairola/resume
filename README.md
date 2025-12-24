
<!-- Install the builder -->

pip install jinja_static/;

jinjastatic --help;

<!-- Run dev server -->
deactivate; rm -r .venv/; python3 -m venv .venv; source .venv/bin/activate;
pip install jinja_static/;
jinjastatic --dev;

