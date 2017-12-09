#!/usr/bin/python

import sys
import Adafruit_DHT
import time
import subprocess
import signal
import os

def read_config():
	global target, error, min_humidity, max_humidity
	config_file = os.path.join(os.path.dirname(__file__), 'config.txt')
	if os.path.isfile(config_file):
		with open(config_file, 'r') as f:
			params = f.read().replace('\n', '').split()
			print len(params)
			if len(params) > 0:
				target = float(params[0])
			if len(params) > 1:
				error = float(params[1])
			output('Target = %.1f : Error = %.1f' % (target, error))
	min_humidity = target - error
	max_humidity = target + error

def get_power_status(outlet):
	global power
	output = int(subprocess.check_output(['sispmctl', '-qng', str(outlet)]).strip())
	if output == 1:
		power = True
	else:
		power = False
	return power

def power_on(outlet):
	global power
	if not power:
		print 'Powering on'
		subprocess.call(['sispmctl', '-qo', str(outlet)])
		power = True

def power_off(outlet):
	global power
	if power:
		print 'Powering off'
		subprocess.call(['sispmctl', '-qf', str(outlet)])
		power = False

def dht(sensor, pin):
	global humidity, temperature
	h, t = Adafruit_DHT.read_retry(sensor, pin)
	if h is not None and t is not None:
		humidity, temperature = round(h, 1), round(t, 1)
	return humidity, temperature

def output(message):
	print message

def signal_hup(signal_number, frame):
	read_config()

def signal_term(signal_number, frame):
	global running
	running = False

sensor = Adafruit_DHT.DHT22
pin = 4
target = 50.0
error = 0.7
read_config()
temperature = 25
humidity = (min_humidity + max_humidity) / 2
outlet = 1
power = False
running = True
signal.signal(signal.SIGHUP, signal_hup)
signal.signal(signal.SIGTERM, signal_term)
try:
	while running:
		get_power_status(outlet)
		dht(sensor, pin)
		output('T=%.1f H=%.1f' % (temperature, humidity))
		if humidity <= min_humidity:
			power_on(outlet)
		elif humidity >= max_humidity:
			power_off(outlet)
		for second in range(5):
			if running:
				time.sleep(1)
except KeyboardInterrupt:
	pass
print 'Quitting...'
power_off(outlet)
