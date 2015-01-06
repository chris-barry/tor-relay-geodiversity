# Tor Geodiversity Explorer

The more diverse the tor network is geographically, the more secure it is.
This project aims to help people visualize where most tor nodes are ran (hint: as of 2015 January it's North America and Europe).

## Running

Running is simple:

	python diversity.py > tor.html

Don't query too often, since the data is pulled from [Onionoo](https://onionoo.torproject.org).
If you need to more often, use the `--debug` flag.
That puts you in debug mode and grabs less relays.

## Python Requirements

	Jinja2>=2.7.3
	OnionPy>=0.2.2
	iso3166>=0.6

## License

[Unlicense](http://unlicense.org).
In `LICENSE`.
