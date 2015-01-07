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

def new_dict(name=''):
	return {
		'count':             0,
		'bandwidth':         0,
		'weight':            0,
		'count_percent':     0,
		'bandwidth_percent': 0,
		'weight_percent':    0,
		'real':              name,
		}

def run_stats(nodes):
	stats = {}
	for c in countries:
		# NOTE: This will probably not result in 100% proper names.
		# Python2 does not cooperate nicely with Unicode. :-(
		stats[c.alpha2.lower()] = new_dict(c.name.encode('ascii','ignore'))

	stats['total'] = new_dict('z-total') # Total stats, z is for lexical sorting to last.
	stats['None'] = new_dict('Unknown, GEOIP error.') # For unknown countries.

	# Aggregrate some numbers.
	for relay in relays.relays:
		# We do not want to count relays which are not running.
		if not relay.running or relay.hibernating:
			continue
		try:
			key = ''
			if relay.geo[0] is None:
				key = 'None'
			else:
				key = relay.geo[0]
			stats[key]['count'] += 1
			stats[key]['weight'] += relay.consensus_weight
			stats[key]['bandwidth'] += relay.bandwidth[2] # observed in bytes per second

			stats['total']['count'] += 1
			stats['total']['weight'] += relay.consensus_weight
			stats['total']['bandwidth'] += relay.bandwidth[2]
		except KeyError:
			print relay.geo[0]

	# This helps with math later.
	total = float(stats['total']['count'])
	weight = float(stats['total']['weight'])
	bandwidth = float(stats['total']['bandwidth'])

	# Compare each country to the total.
	for relay in relays.relays:
		# We do not want to count relays which are not running.
		if not relay.running or relay.hibernating:
			continue
		try:
			key = ''
			if relay.geo[0] is None:
				key = 'None'
			else:
				key = relay.geo[0]
			stats[key]['count_percent'] = (stats[key]['count'] / total) * 100
			stats[key]['weight_percent'] = (stats[key]['weight'] / weight) * 100
			stats[key]['bandwidth_percent'] = (stats[key]['bandwidth'] / bandwidth) * 100
		except KeyError:
			print type(relay.geo[0])

	# Sanity - all should be 100% += floating point errors.
	stats['total']['count_percent'] = (stats['total']['count'] / total) * 100
	stats['total']['weight_percent'] = (stats['total']['weight'] / weight) * 100
	stats['total']['bandwidth_percent'] = (stats['total']['bandwidth'] / bandwidth) * 100

	# Sort by country name.
	stats_sorted = []
	keylist = stats.keys()
	keylist.sort()
	for key in keylist:
		stats_sorted.append(stats[key])

	return stats_sorted


# Do the templating
def make_template(template_file="index.html", f="tor.html", stats={}):
	env = Environment(loader=FileSystemLoader('templates'))
	template = env.get_template(template_file)
	f = open(f, "w")
	f.write(template.render(
		stats=stats,
		time=datetime.datetime.now(),
		number_format='{:,}',
		percent_format='{0:0.2f}')
	)
	f.close()

# Real work starts here.
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='Enable debug settings', action='store_true')
	parser.add_argument('-f', '--output-file', help='Where to save file', type=str, default="tor.html")
	parser.add_argument('-t', '--template-file', help='What template to use, only HTML made right now', type=str, default="index.html")
	args = parser.parse_args()

	relays = get_relays(debug=args.debug)
	stats = run_stats(nodes=relays)
	make_template(template_file=args.template_file, f=args.output_file, stats=stats)
