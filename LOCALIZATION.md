# How to localize

*hydra_login2f* uses [babel](http://babel.pocoo.org/en/latest/) for
localization. Here are the most basic commands that you will probably
want to use (they all should be executed from the `hydra_login2f/`
directory):

## Extract all messages to `messages.pot`:

```
$ pipenv run pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```

## Update all `.po` files from `messages.pot`

```
$ pipenv run pybabel update -i messages.pot -d translations
```

## Compile all `.po` files to `.mo` files

```
$ pipenv run pybabel compile -d translations
```

## Create translation for a new language:

```
$ pipenv run pybabel init -i messages.pot -d translations -l de
```
