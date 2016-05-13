################################################################################
#
#  Copyright 2007-2016 Jeffrey Newman.
#
#  This file is part of Larch.
#
#  Larch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Larch is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Larch.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
#
#  This example file shows commands needed to replicate the models given in 
#  the Field Guide to Discrete Choice Models.
#
################################################################################

from .. import larch

def data():
	# Define which data set to use with this example.
	return larch.DB.Example('MTC')

def model(d=None): # Define a function to create a data object.
	m = larch.Model.loads("# saved at 10:08:05 PM CST on 26 Feb 2016\nself.title = _Str('VW50aXRsZWQgTW9kZWw=')\n\nself.parameter(_Str('QVNDX1NSMg=='), value=float.fromhex('-0x1.16c9fd4c2115fp+1'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('QVNDX1NSM1A='), value=float.fromhex('-0x1.dcd12ec42d127p+1'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('QVNDX1RSQU4='), value=float.fromhex('-0x1.5789c9a5945f4p-1'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('QVNDX0JJS0U='), value=float.fromhex('-0x1.302c02f1cf925p+1'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('QVNDX1dBTEs='), value=float.fromhex('-0x1.a78de88a2de77p-3'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('aGhpbmMjMg=='), value=float.fromhex('-0x1.1c6d2c8ef6289p-9'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('aGhpbmMjMw=='), value=float.fromhex('0x1.77079ade395a2p-12'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('aGhpbmMjNA=='), value=float.fromhex('-0x1.5a745d8d634e8p-8'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('aGhpbmMjNQ=='), value=float.fromhex('-0x1.a3b1ba3a4712dp-7'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('aGhpbmMjNg=='), value=float.fromhex('-0x1.3d6644d6867e8p-7'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('dG90dGltZQ=='), value=float.fromhex('-0x1.a494af98b5f21p-5'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\nself.parameter(_Str('dG90Y29zdA=='), value=float.fromhex('-0x1.42752ab05775p-8'), null_value=0, initial_value=0, max=inf, min=-inf, holdfast=False)\n\n\nself.utility.ca(_Str('dG90dGltZQ=='),_Str('dG90dGltZQ=='),1)\nself.utility.ca(_Str('dG90Y29zdA=='),_Str('dG90Y29zdA=='),1)\nself.utility.co(2,_Str('MQ=='),_Str('QVNDX1NSMg=='),1)\nself.utility.co(2,_Str('aGhpbmM='),_Str('aGhpbmMjMg=='),1)\nself.utility.co(3,_Str('MQ=='),_Str('QVNDX1NSM1A='),1)\nself.utility.co(3,_Str('aGhpbmM='),_Str('aGhpbmMjMw=='),1)\nself.utility.co(4,_Str('MQ=='),_Str('QVNDX1RSQU4='),1)\nself.utility.co(4,_Str('aGhpbmM='),_Str('aGhpbmMjNA=='),1)\nself.utility.co(5,_Str('MQ=='),_Str('QVNDX0JJS0U='),1)\nself.utility.co(5,_Str('aGhpbmM='),_Str('aGhpbmMjNQ=='),1)\nself.utility.co(6,_Str('MQ=='),_Str('QVNDX1dBTEs='),1)\nself.utility.co(6,_Str('aGhpbmM='),_Str('aGhpbmMjNg=='),1)\n\n\nself.root_id = 0\n\nself._set_estimation_statistics(float.fromhex('-0x1.c545f5ccd78dp+11'),float.fromhex('-0x1.c8d99d948da7cp+12'),nan,nan,float.fromhex('-0x1.c545f5ccd78dp+11'))\nself._set_estimation_run_statistics_pickle('gAN9cQAoWA4AAABudW1iZXJfdGhyZWFkc3EBSwhYBwAAAHJlc3VsdHNxAlgHAAAAc3VjY2Vzc3EDWAkAAABwcm9jZXNzb3JxBFgEAAAAaTM4NnEFWBAAAABudW1iZXJfY3B1X2NvcmVzcQZLCFgFAAAAbm90ZXNxB11xCFglAAAAZGlkIG5vdCBhdXRvbWF0aWNhbGx5IHJlc2NhbGUgd2VpZ2h0c3EJYVgJAAAAdGltZXN0YW1wcQpYJQAAAEZyaWRheSwgRmVicnVhcnkgMjYgMjAxNiwgMTA6MDc6NDcgUE1xC1gLAAAAX290aGVyX2F0dHJxDH1xDVgJAAAAaXRlcmF0aW9ucQ5LClgRAAAAcHJvY2Vzc19zdGFydHRpbWVxD11xEChKj+9Mfkrb70x+St7vTH5K3u9Mfkrf70x+SlbwTH5KwPBMfmVYDwAAAHByb2Nlc3NfZW5kdGltZXERXXESKErb70x+St7vTH5K3u9Mfkre70x+SlXwTH5KwPBMfkrA8Ex+ZVgWAAAAdG90YWxfZHVyYXRpb25fc2Vjb25kc3ETRz/TZFocrAgxWA0AAABwcm9jZXNzX2xhYmVscRRdcRUoWAUAAABzZXR1cHEWWA8AAABudWxsX2xpa2VsaWhvb2RxF1gXAAAAd2VpZ2h0IGNob2ljZSByZWJhbGFuY2VxGFgSAAAAd2VpZ2h0IGF1dG9yZXNjYWxlcRlYDQAAAG9wdGltaXplOmJoaGhxGlgUAAAAcGFyYW1ldGVyIGNvdmFyaWFuY2VxG1gHAAAAY2xlYW51cHEcZVgRAAAAcHJvY2Vzc19kdXJhdGlvbnNxHV1xHihYBwAAADA6MDAuMDhxH1gEAAAAMDowMHEgWAQAAAAwOjAwcSFYBAAAADA6MDBxIlgHAAAAMDowMC4xMnEjWAcAAAAwOjAwLjExcSRYBAAAADA6MDBxJWVYDgAAAHRvdGFsX2R1cmF0aW9ucSZYBgAAADA6MDAuM3EndS4=')\n\nself.option.threads= 8\nself.option.calc_null_likelihood= True\nself.option.null_disregards_holdfast=True\nself.option.calc_std_errors= True\nself.option.gradient_diagnostic= 0\nself.option.hessian_diagnostic= 0\nself.option.mute_nan_warnings= True\nself.option.force_finite_diff_grad= False\nself.option.force_recalculate= False\nself.option.save_db_hash= False\nself.option.author= 'Chuck Finley'\nself.option.teardown_after_estimate= True\nself.option.weight_autorescale= True\nself.option.weight_choice_rebalance= True\nself.option.suspend_xylem_rebuild= False\nself.option.log_turns= False\nself.option.enforce_bounds= True\nself.option.enforce_constraints= False\nself.option.idca_avail_ratio_floor= 0.1\n\nself.recall(nCases=5029)\nself.covariance_matrix = numpy.loads( base64.standard_b64decode('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'))\nself.robust_covariance_matrix = numpy.loads( base64.standard_b64decode('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'))\nimport pickle\n\nself.descriptions = pickle.loads(b'\\x80\\x03clarch.util.attribute_dict\\ndicta\\nq\\x00)\\x81q\\x01.')\n")
	return m

############################# END OF EXAMPLE FILE ##############################

