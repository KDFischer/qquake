#/***************************************************************************
# QQuake
#
# QQuake plugin to download seismologic data
#                                                       -------------------
#              begin                           : 2019-11-20
#              git sha                         : $Format:%H$
#              copyright                       : (C) 2019 by Faunalia
#              email                           : matteo.ghetta@faunalia.eu
# ***************************************************************************/
#
#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################

# Add iso code for any locales you want to support here (space separated)
# default is no locales
LOCALES = af

# If locales are enabled, set the name of the lrelease binary on your system. If
# you have trouble compiling the translations, you may have to specify the full path to
# lrelease
LRELEASE ?= lrelease-qt5

# QGIS3 default
QGISDIR=.local/share/QGIS/QGIS3/profiles/default


# translation
SOURCES = \
    qseismo/__init__.py \
    qseismo/qquake.py \
    qseismo/qquake_dialog.py

PLUGIN_NAME = qseismo

EXTRAS = metadata.txt icon.png icon.svg

EXTRA_DIRS =

PEP8EXCLUDE=pydev,conf.py,third_party,ui

default:

%.qm : %.ts
	$(LRELEASE) $<

test: transcompile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests3 -v -s --with-id --with-coverage --cover-package=. $(PLUGIN_NAME).test \
		3>&1 1>&2 2>&3 3>&- || true
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core error, try sourcing"
	@echo "the helper script we have provided first then run make test."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make test"
	@echo "----------------------"


deploy:
	@echo
	@echo "------------------------------------------"
	@echo "Deploying (symlinking) plugin to your qgis3 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)/python/plugins
	ln -s `pwd`/qgis-r $(HOME)/$(QGISDIR)/python/plugins/${PWD##*/}


transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x scripts/update-strings.sh
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LRELEASE) $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc $(PLUGIN_NAME)
	@echo
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core' error, try sourcing"
	@echo "the helper script we have provided first then run make pylint."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make pylint"
	@echo "----------------------"


# Run pep8/pycodestyle style checking
#http://pypi.python.org/pypi/pep8
pycodestyle:
	@echo
	@echo "-----------"
	@echo "pycodestyle PEP8 issues"
	@echo "-----------"
	@pycodestyle --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128,E402,E501,W504 --exclude $(PEP8EXCLUDE) $(PLUGIN_NAME)
	@echo "-----------"
	@echo "Ignored in PEP8 check:"
	@echo $(PEP8EXCLUDE)

# The dclean target removes compiled python files from plugin directory
# also deletes any .git entry
dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find $(PLUGIN_NAME) -iname "*.pyc" -delete
	find $(PLUGIN_NAME) -iname ".git" -prune -exec rm -Rf {} \;

zip: dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org
	rm -f $(PLUGIN_NAME).zip
	zip -9r $(PLUGIN_NAME).zip $(PLUGIN_NAME) -x *.git* -x *__pycache__* -x *test*
