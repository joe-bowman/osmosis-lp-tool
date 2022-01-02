#!/usr/bin/python3
'''
   Copyright 2022 Joe Bowman

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import requests
import sys


## TODO: utilise click for args
def usage():
  print("Usage: {} <bech32_addr> [--csv]".format(sys.argv[0]))
  sys.exit()

if len(sys.argv) < 2:
  usage()

if len(sys.argv) > 3:
  usage()

if len(sys.argv) == 3 and sys.argv[2] != '--csv':
  usage()

if len(sys.argv) == 3 and sys.argv[2] == '--csv':
  format = 'csv'
else:
  format = 'text'

input_address = sys.argv[1]
## TODO: verify bech32

## fetch list of locked tokens for the given account
act = requests.get('https://lcd-osmosis.keplr.app/osmosis/lockup/v1beta1/account_locked_coins/{}'.format(input_address))
out = act.json()

tokens = {}

print("Processing pools...")
## iterate over pool tokens account holds; fetch pool data and work out what our slice of the total locked assets is.
for idx, coin in enumerate(out.get('coins')):
  pool = coin.get('denom').split('/')[-1]
  info = requests.get('https://lcd-osmosis.keplr.app/osmosis/gamm/v1beta1/pools/{}'.format(pool))
  coin_info = info.json().get('pool')
  ## percentage slice of the pie.
  slice = float(coin.get('amount'))/float(coin_info.get('totalShares').get('amount'))
  for token in coin_info.get('poolAssets'):
    denom = token.get('token').get('denom')
    tokens.update({denom: tokens.get(denom, 0) + int(token.get('token').get('amount'))*slice})
  print("Done {}/{}".format(idx+1, len(out.get('coins'))))

tokens_out = {}

print("Processing denoms...")
## fetch pools data with symbols & prices; iterate over this until we have data for all our tokens.
pools = requests.get('https://api-osmosis.imperator.co/search/v1/pools').json()
for idx, denom in enumerate(tokens.keys()):
  try:
    for _, p in pools.items():
      for t in p:
        if t.get('denom') == denom:
          tokens_out.update({denom: {'amount': tokens.get(denom)/1e6, 'symbol': t.get('symbol'), 'price': t.get('price')}})
          print('Done {}/{}'.format(idx+1, len(tokens)))
          ## short circuit to avoid unneccessary iterations
          raise Exception
  except:
    pass

## print csv or plaintext output.
if format == 'csv':
  print()
  print("DENOM,AMOUNT,PRICE_PER,TOTAL")
  for _, value in tokens_out.items():
    print("{},{},{},{}".format(value.get('symbol'), value.get('amount'), value.get('price'), float(value.get('price'))*value.get('amount')))

else:
  for _, value in tokens_out.items():
    print("{}: {} @ {} USD = {} USD".format(value.get('symbol'), value.get('amount'), value.get('price'), float(value.get('price'))*value.get('amount')))

# fin.
