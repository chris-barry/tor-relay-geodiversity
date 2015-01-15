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
import math
import shutil
import sys
import os
import pprint


# Get relay information from Onionoo
def get_relays(debug=False, host=''):
	manager = Manager(OnionSimpleCache(), onionoo_host=host)
	try:
		if args.debug:
			s = manager.query('details', limit=9)
		else:
			s = manager.query('details')
	except:
		print 'Problem with Onionoo: ', sys.exc_info()[0]
		sys.exit()
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

def bucket_num(num=0, bucket_size=10, scale=0.50):
	if num == 0:
		l = 0
	else:
		l = (math.log(num)*scale / bucket_size) // 1
	d = ''
	if num <= 0 or l == 0:
		 d = 'None'
	if num > 0 or l == 1:
		 d = 'one'
	if l == 2:
		 d = 'two'
	if l == 3:
		 d = 'three'
	if l == 4:
		 d = 'four'
	if l == 5:
		 d = 'five'
	if l == 6:
		 d = 'six'
	if l == 7:
		 d = 'seven'
	if l >= 8:
		 d = 'eight'
	return d

def get_ranges(ranges=10, min=0, max=0):
	bucket_size = math.log(max)/ranges
	r = [0] * (ranges + 1)

	if min == 0:
		r[0] = 0
	else:
		r[0] = math.log(total['count_min'])

	for x in range(1, ranges):
		r[x] = bucket_size * x

	r[ranges] = math.log(max)

	return r

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
			stats[key]['exit_probability'] += (relay.exit_probability * 100)
			stats[key]['as'][relay.as_number] = 1
		
			total['count'] += 1
			total['weight'] += relay.consensus_weight
			total['bandwidth'] += relay.bandwidth[2]
			total['exit_probability'] += (relay.exit_probability * 100)
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

		# Averages
		total['as_avg'] = len(total['as']) / countries_total
		total['bandwidth_avg'] = total['bandwidth'] / countries_total
		total['count_avg'] = total['count'] / countries_total
		total['exit_probability_avg'] = total['exit_probability'] / countries_total
		total['weight_avg'] = total['weight'] / countries_total

		# Ranges
		if len(stats[key]['as']) <= total['as_min'] and len(stats[key]['as']) > 0:
			total['as_min'] = len(stats[key]['as'])
		if len(stats[key]['as']) >= total['as_max']:
			total['as_max'] = len(stats[key]['as'])

		if stats[key]['bandwidth'] <= total['bandwidth_min'] and stats[key]['bandwidth'] > 0:
			total['bandwidth_min'] = stats[key]['bandwidth']
		if stats[key]['bandwidth'] >= total['bandwidth_max']:
			total['bandwidth_max'] = stats[key]['bandwidth']

		if stats[key]['count'] <= total['count_min'] and stats[key]['count'] > 0:
			total['count_min'] = stats[key]['count']
		if stats[key]['count'] >= total['count_max']:
			total['count_max'] = stats[key]['count']

		if stats[key]['exit_probability'] <= total['exit_probability_min'] and stats[key]['exit_probability'] > 0:
			total['exit_probability_min'] = stats[key]['exit_probability']
		if stats[key]['exit_probability'] >= total['exit_probability_max']:
			total['exit_probability_max'] = stats[key]['exit_probability']
		
		if stats[key]['weight'] <= total['weight_min'] and stats[key]['weight'] > 0:
			total['weight_min'] = stats[key]['weight']
		if stats[key]['weight'] >= total['weight_max']:
			total['weight_max'] = stats[key]['weight']

	as_range = get_ranges(ranges=11, min=total['as_min'], max=total['as_max'])
	bandwidth_range = get_ranges(ranges=11, min=total['bandwidth_min'], max=total['bandwidth_max'])
	count_range = get_ranges(ranges=11, min=total['count_min'], max=total['count_max'])
	exit_range = get_ranges(ranges=11, min=total['exit_probability_min'], max=total['exit_probability_max'])
	weight_range = get_ranges(ranges=11, min=total['weight_min'], max=total['weight_max'])

	for c in countries:
		key = c.alpha2.lower()
		stats[key]['as_q'] = bucket_num(num=len(stats[key]['as']),            bucket_size=as_range[1]-as_range[0])
		stats[key]['bandwidth_q'] = bucket_num(num=stats[key]['bandwidth'],   bucket_size=bandwidth_range[1]-bandwidth_range[0])
		stats[key]['count_q'] = bucket_num(num=stats[key]['count'],           bucket_size=count_range[1]-count_range[0])
		stats[key]['exit_q'] = bucket_num(num=stats[key]['exit_probability'], bucket_size=exit_range[1]-exit_range[0])
		stats[key]['weight_q'] = bucket_num(num=stats[key]['weight'],         bucket_size=weight_range[1]-weight_range[0])

	# Sanity - all should be 100%.
	total['count_pct'] = (total['count'] / float(total['count'])) * 100
	total['bandwidth_pct'] = (total['bandwidth'] / bandwidth) * 100
	total['weight_pct'] = (total['weight'] / weight) * 100

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
		time=str(datetime.datetime.utcnow())[:-3],
		number_format='{:,}',
		percent_format='{0:0.2f}')
	f = open(os.path.join(out_dir, template_file), 'w')
	f.write(s)
	f.close()


# Real work starts here.
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='Enable debug settings', action='store_true')
	parser.add_argument('-o', '--output-dir', help='Output directory', type=str, default='output/')
	parser.add_argument('-i', '--onionoo-instance', help='Onionoo instance to use', type=str, default='https://onionoo.torproject.org/')
	args = parser.parse_args()

	relays = get_relays(debug=args.debug, host=args.onionoo_instance)
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

