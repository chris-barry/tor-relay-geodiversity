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

import argparse
import datetime
import shutil
import os
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
		'count_percent':     0,
		'bandwidth':         0,
		'bandwidth_percent': 0,
		'weight':            0,
		'weight_percent':    0,
		'exit_probability':  0,
		'country_name':      name,
		'as':                {},
		'family':            {},
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
			stats[key]['exit_probability'] += relay.exit_probability
			stats[key]['as'][relay.as_number] = 1

			if relay.family is not None:
				for family in relay.family:
					stats[key]['family'][family] = 1
					stats['total']['family'][family] = 1

			stats['total']['count'] += 1
			stats['total']['weight'] += relay.consensus_weight
			stats['total']['bandwidth'] += relay.bandwidth[2]
			stats['total']['exit_probability'] += relay.exit_probability
			stats['total']['as'][relay.as_number] = 1
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
			# NOTE: we don not include exit_probability since it will go to 1.0 itself.
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
def make_template(stats={}, out_dir='.', template_file='index.html'):
	env = Environment(loader=FileSystemLoader('templates'))
	template = env.get_template(template_file)
	s = template.render(
		stats=stats,
		time=datetime.datetime.utcnow(),
		number_format='{:,}',
		percent_format='{0:0.2f}')
	f = open(os.path.join(out_dir, template_file), 'w')
	f.write(s)
	f.close()


# Real work starts here.
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='Enable debug settings', action='store_true')
	parser.add_argument('-o', '--output-dir', help='Where to save file', type=str, default='output/')
	args = parser.parse_args()

	relays = get_relays(debug=args.debug)
	stats = run_stats(nodes=relays)
	make_template(stats=stats, out_dir=args.output_dir, template_file='index.html')
	make_template(stats=stats, out_dir=args.output_dir, template_file='tabulated.html')


	try:
		shutil.rmtree(os.path.join(args.output_dir, 'js'))
		shutil.rmtree(os.path.join(args.output_dir, 'css'))
	except:
		pass # we don't care if it fails.

	shutil.copytree('templates/js', os.path.join(args.output_dir, 'js'), symlinks=False, ignore=None)
	shutil.copytree('templates/css', os.path.join(args.output_dir, 'css'), symlinks=False, ignore=None)

