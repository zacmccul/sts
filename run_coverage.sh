coverage run -m unittest unittests.py
coverage report
coverage html
rm assets/coverage.svg
coverage-badge -o assets/coverage.svg
