style:
	isort --profile black .
	black .

check:
	# Ignore:
    # E501 line too long
	flake8 --ignore=E501 .
