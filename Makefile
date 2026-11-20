# make all  -> regenerate everything (data, models, docs, deck) and run tests
PY ?= python

.PHONY: all data model mix docs deck app test pdf
all:
	$(PY) run_all.py
data:
	$(PY) -m src.clean && $(PY) -m src.geo
model:
	$(PY) -m src.forecast.run
mix:
	$(PY) -m src.mix
docs:
	$(PY) -m src.docs_build && $(PY) -m src.regional_cards && $(PY) -m src.report_figs
deck:
	node deck/build_deck.js
pdf:
	pandoc docs/methodology.md -o docs/methodology.pdf --pdf-engine=wkhtmltopdf --toc
app:
	streamlit run dashboard/app.py
test:
	$(PY) -m pytest -q tests
