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

def new_dict(name='', name3='NONE'):
	return {
		'count':             0,
		'count_percent':     0,
		'bandwidth':         0,
		'bandwidth_percent': 0,
		'weight':            0,
		'weight_percent':    0,
		'exit_probability':  0,
		'country_name':      name,
		'country_name3':     name3,
		'as':                {},
		'count_q':           '',
		}

def run_stats(nodes):
	stats = {}
	for c in countries:
		# NOTE: This will probably not result in 100% proper names.
		# Python2 does not cooperate nicely with Unicode. :-(
		stats[c.alpha2.lower()] = new_dict(c.name.encode('ascii','ignore'), c.alpha3)
	stats['None'] = new_dict('Unknown, GEOIP error.') # For unknown countries.

	# Total is stored in a different structure to make retreiving stats easier.
	total = {
		'countries': 0,
		'countries_seen': 0,

		'as'      : {},
		'as_pct'  : 0,
		'as_min'  : 0,
		'as_avg'  : 0,
		'as_max'  : 0,

		'count'      : 0,
		'count_pct'  : 0,
		'count_min'  : 0,
		'count_avg'  : 0,
		'count_max'  : 0,

		'bandwidth'      : 0,
		'bandwidth_pct'  : 0,
		'bandwidth_min'  : 0,
		'bandwidth_avg'  : 0,
		'bandwidth_max'  : 0,

		'exit_probability'      : 0,
		'exit_probability_pct'  : 0,
		'exit_probability_min'  : 0,
		'exit_probability_avg'  : 0,
		'exit_probability_max'  : 0,

		'weight'      : 0,
		'weight_pct'  : 0,
		'weight_min'  : 0,
		'weight_avg'  : 0,
		'weight_max'  : 0,
	}

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

			""" # This does not do what I thought it would.
			if relay.family is not None:
				for family in relay.family:
					stats[key]['family'][family] = 1
					total['family'][family] = 1
			"""

			total['count'] += 1
			total['weight'] += relay.consensus_weight
			total['bandwidth'] += relay.bandwidth[2]
			total['exit_probability'] += relay.exit_probability
			total['as'][relay.as_number] = 1
		except KeyError:
			print relay.geo[0]
	
	total['countries_seen'] = float(len(stats))
	total['countries'] = float(len(countries))
	
	# The floats helps with math later.
	bandwidth = float(total['bandwidth'])
	countries_total = float(total['countries_seen'])
	weight = float(total['weight'])

	total['as_average'] = len(total['as']) / countries_total 
	total['bandwidth_avg'] = total['bandwidth'] / countries_total 
	total['count_avg'] = total['count'] / countries_total 
	total['exit_probability_avg'] = total['exit_probability'] / countries_total 
	total['weight_avg'] = total['weight'] / countries_total 

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
			stats[key]['bandwidth_percent'] = (stats[key]['bandwidth'] / bandwidth) * 100
			stats[key]['count_percent'] = (stats[key]['count'] / float(total['count'])) * 100
			stats[key]['weight_percent'] = (stats[key]['weight'] / weight) * 100
			# NOTE: we do not include exit_probability since it will go to 1.0 itself.
		except KeyError:
			print relay.geo[0]

		total['as_avg'] = len(total['as']) / countries_total
		total['bandwidth_avg'] = total['bandwidth'] / countries_total
		total['count_avg'] = total['count'] / countries_total
		total['exit_probability_avg'] = total['exit_probability'] / countries_total
		total['weight_avg'] = total['weight'] / countries_total

		for c in countries:
			key = c.alpha2.lower()
			# Do the quintiles for the number of nodes per country.
			c = stats[key]['count'] - total['count_avg']
			# Get mean difference, use it to make some standard deviation plot.
			if c > 0 and c < 10 :
				stats[key]['count_q'] = 'Over_1'
			if c > 0 and c < 20 :
				stats[key]['count_q'] = 'Over_2'
			if c > 0 and c < 30 :
				stats[key]['count_q'] = 'Over_3'
			if c > 0 and c > 40:
				stats[key]['count_q'] = 'Over_4'

			if c < 0 and c < -10:
				stats[key]['count_q'] = 'Under_1'
			if c < 0 and c < -20:
				stats[key]['count_q'] = 'Under_2'
			if c < 0 and c < -30:
				stats[key]['count_q'] = 'Under_3'
			if c < -40:
				stats[key]['count_q'] = 'Under_4'
			if c == 0:
				stats[key]['count_q'] = 'Equal'

			if stats[key]['count'] == 0:
				stats[key]['count_q'] = 'None'

	# Sanity - all should be 100%.
	total['count_pct'] = (total['count'] / float(total['count'])) * 100
	total['weight_pct'] = (total['weight'] / weight) * 100
	total['bandwidth_pct'] = (total['bandwidth'] / bandwidth) * 100

	#pprint.pprint(total)

	# Sort by country name.
	stats_sorted = []
	keylist = stats.keys()
	keylist.sort()
	for key in keylist:
		stats_sorted.append(stats[key])

	return (stats_sorted, total)


# Do the templating
def make_template(stats={}, total={}, out_dir='.', template_file='index.html'):
	env = Environment(loader=FileSystemLoader('templates'))
	template = env.get_template(template_file)
	s = template.render(
		stats=stats,
		total=total,
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
	stats, total = run_stats(nodes=relays)

	make_template(stats=stats, total=total, out_dir=args.output_dir, template_file='index.html')
	make_template(stats=stats, total=total, out_dir=args.output_dir, template_file='tabulated.html')
	make_template(stats=stats, total=total, out_dir=args.output_dir, template_file='mapped-count.html')

	try:
		shutil.rmtree(os.path.join(args.output_dir, 'js'))
		shutil.rmtree(os.path.join(args.output_dir, 'css'))
	except:
		pass # we don't care if it fails.

	shutil.copytree('templates/js', os.path.join(args.output_dir, 'js'), symlinks=False, ignore=None)
	shutil.copytree('templates/css', os.path.join(args.output_dir, 'css'), symlinks=False, ignore=None)

