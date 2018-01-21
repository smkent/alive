# alive: Send a preconfigured email via a tweet

alive is a cron-based tool that sends a user pre-defined email if the user
tweets a particular message.

I wrote this to provide an easy way to notify several people at once that I am
safe in the event I survive a natural disaster. Following such an event, it is
likely that network access may be disrupted or severely limited. This tool
allows sending an email by tweeting a specific message, which itself can be
created by simply texting the desired message to Twitter's shortcode.

I chose this architecture as text messages are one of, if not the lowest
bandwidth form of network communication commonly available, and as such is most
likely to be available in a limited access situation.

This tool works best when deployed in a different geographic location than where
you live, to increase the chances that it will be available following a local
natural disaster.

## Dependencies and usage overview

Once installed and configured, alive's outgoing email message can be triggered
by:
* Tweeting a message starting with the word `alive`, preferably by texting the
  tweet to [Twitter's short code][twitter-sms] (`40404` in the US) after adding
  your phone number to your Twitter account. The trigger word(s) are
  configurable.
* Running the `alive` utility interactively.

When sending an email, if standard input is connected to a console, PGP signing
is attempted on the outgoing email using [GnuPG][gnupg]. If successful, this
provides the recipient(s) an additional tool to verify the message was sent by
you, and is most useful if the message was sent from the interactive `alive`
utility.

alive provides two executables:

* `alive-check`: A polling script meant to be run by cron. This checks Twitter
  for new messages.
* `alive`: A script used to trigger the outgoing email interactively.

alive requires:
* Python 3
* [pipenv][pipenv] for virtualenv creation and dependency installation
* A [Twitter API key][twitter-api] and an application-specific access token.
  Refer to the Twitter API documentation for more information.
* cron for checking for tweets
* sendmail

## Installation

alive uses [pipenv][pipenv] to manage its virtualenv and dependencies. Install
pipenv:

```shell
$ pip install pipenv
```

To configure alive, simply run:

```shell
$ ./setup
```

which will create a virtualenv in the repository directory and install all the
needed dependencies.

## Configuration

### Outgoing email

alive stores its configuration by default in `~/.alive/config.yaml`. Start by
adding the desired outgoing message configuration:

File: `~/.alive/config.yaml`
```yaml
email:
  from: 'Alice <alice@example.com>'
  to:
    - 'Bob <bob@example.com>'
    - 'Carol <carol@example.com>'
  subject: Alive message
  message: >
    This email is being sent to you automatically to let you know I am safe.
```

Notes:
* `to` supports either single or multiple recipients. `cc` and `bcc`
  configuration keys are also supported (and may have multiple recipients as
  well).
* `message` may contain inline message text or a full path to a file name. If
  the value of `message` is a file path, that file will be read and its contents
  used as the message instead.
* `attachments` may be added, with a list of file(s) to attach to the outgoing
  email.

`from` and `to` are required. If not provided, the default value of `message` is
an empty string, and the default value of `subject` is `Safety information
message`.

### Twitter

To poll tweets, you will need to create a [Twitter API key][twitter-api] and an
application-specific access token.

After obtaining Twitter API access, add the following settings to the
configuration file:

File: `~/.alive/config.yaml`
```yaml
twitter:
  username: your-twitter-username
  consumer_key: (Twitter API consumer key)
  consumer_secret: (Twitter API consumer secret)
  access_token_key: (Twitter API app access token key)
  access_token_secret: (Twitter API app access token secret)
  keyword: alive
```

If not specified, the default value for `keyword` is `alive`.

### Monthly testing

By default, alive will send a test message once per month in order to manually
verify the system is still working properly. This can be disabled (or the
interval changed) by adding the following configuration:

File: `~/.alive/config.yaml`
```yaml
periodic_test:
  enabled: False   # Enable or disable sending periodic test messages
  interval: 86400  # Minimum number of seconds between test messages
```

### cronjob

Finally, configure a cronjob to check for new tweets on a schedule using the
`bin/alive-check` utility created by `./setup`.

For example, to check for new Tweets once every 5 minutes, use:

```
*/5 * * * * /full/path/to/alive/bin/alive-check
```

Add this to your crontab by running `crontab -e` and adding the line to the end
of the file.

## Testing

To test that everything is set up, do one of the following:

* Execute `bin/alive --test` from the repository directory
* Tweet a message beginning with `alive` (or one of the configured keyword(s))
  and with `test` as the second word in the tweet (`alive test`, for example).

A test message is the same as the normal message, except the test message
contains `[TEST MESSAGE]` in the subject line and is only sent to the `email`
`from` address in the configuration file instead of the normal recipients.

## Debugging

`alive` and `alive-check` may be invoked with the `--debug` option to print any
generated outgoing email(s) to standard output instead of passing them to
sendmail.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

See [`LICENSE`](/LICENSE) for the full license text.

[gnupg]: https://www.gnupg.org/
[pipenv]: https://github.com/pypa/pipenv
[twitter-api]: https://apps.twitter.com/
[twitter-sms]: https://help.twitter.com/en/using-twitter/supported-mobile-carriers
