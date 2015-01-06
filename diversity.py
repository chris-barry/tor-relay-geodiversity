# -*- coding: utf-8 -*-
# diversity.py - Geodiversity information about the tor network.
#
# Chris Barry <chris@barry.im>
#
# License: The Unlicense, see LICENSE.

from iso3166 import countries
from jinja2 import Environment, PackageLoader, FileSystemLoader
from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache
import datetime
import argparse

import pprint


# Get relay information from Onionoo
def get_relays(debug=False):
	manager = Manager(OnionSimpleCache())
	if args.debug:
		s = manager.query('details', limit=9)
	else:
		s = manager.query('details')
	return s

def run_stats(nodes):
	stats = {}
	for c in countries:
		stats[c.alpha2.lower()] = {
		'count':     0,
		'bandwidth': 0,
		'weight':    0,
		# NOTE: This will probably not result in 100% proper names.
		# Python2 does not cooperate nicely with Unicode. :-(
		'real':      c.name.encode('ascii','ignore')
		}

	# Keep count of everything we have seen.
	stats['total'] = {
		'count':     0,
		'bandwidth': 0,
		'weight':    0,
		'real':      'z-total', # the z makes it last in the list of countries.
	}

	# Aggregrate some numbers.
	for relay in relays.relays:
		# We do not want to count relays which are not running.
		if not relay.running or relay.hibernating:
			continue

		try:
			stats[relay.geo[0]]['count'] += 1
			stats[relay.geo[0]]['weight'] += relay.consensus_weight
			stats[relay.geo[0]]['bandwidth'] += relay.bandwidth[2] # observed in	bytes per second

			stats['total']['count'] += 1
			stats['total']['weight'] += relay.consensus_weight
			stats['total']['bandwidth'] += relay.bandwidth[2] # observed in	bytes per second
		except KeyError:
			# NOTE:
			# Currently this happens if there is a country we don't know from iso3166.
			# None seems to be the only one as of now.
			# This is hackish but understandable to need this code path.
			stats[relay.geo[0]] = {
				'count':    1,
				'bandwidth': relay.bandwidth[2],
				'weight':   relay.consensus_weight,
				'real':     relay.geo[1],
			}
	# Sort by country name.
	stats_sorted = []
	keylist = stats.keys()
	keylist.sort()
	for key in keylist:
		stats_sorted.append(stats[key])

	return stats_sorted


def make_template(template_file="index.html", f="tor.html", stats={}):
	# Do the templating
	env = Environment(loader=FileSystemLoader('templates'))
	template = env.get_template(template_file)
	f = open(f, "w")
	f.write(template.render(stats=stats, time=datetime.datetime.now()))
	f.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='Enable debug settings', action='store_true')
	parser.add_argument('-f', '--output-file', help='Where to save file', type=str, default="tor.html")
	parser.add_argument('-t', '--template-file', help='What template to use, only HTML made right now', type=str, default="index.html")
	args = parser.parse_args()

	# Real work starts here.
	relays = get_relays(debug=args.debug)
	stats = run_stats(nodes=relays)
	make_template(template_file=args.template_file, f=args.output_file, stats=stats)
