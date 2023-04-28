PHONY: status

style:
	isort --profile black .
	black .

check:
	isort --profile black . --check
	black . --check
	# Ignore:
    # E501 line too long
	flake8 --ignore=E501 --exclude=helpers . 
	mypy --exclude=helpers .

status:
	./status.sh
