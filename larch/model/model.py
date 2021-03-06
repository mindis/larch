import pandas
import numpy
import copy

from .controller import Model5c as _Model5c
from ..dataframes import DataFrames
from ..roles import LinearFunction
from ..general_precision import l4_float_dtype

class Model(_Model5c):

	@classmethod
	def Example(cls, n=1):
		from ..examples import example
		return example(n)

	def __init__(self, *args, **kwargs):
		self._sklearn_data_format = 'idce'
		super().__init__(*args, **kwargs)

	def get_params(self, deep=True):
		p = dict()
		if deep:
			p['frame'] = self.pf.copy()
			p['utility_ca'] = LinearFunction(self.utility_ca.copy())
			p['utility_co'] = self.utility_co.copy_without_touch_callback()
			p['quantity_ca'] = LinearFunction(self.quantity_ca.copy())
			p['quantity_scale'] = self.quantity_scale.copy() if self.quantity_scale is not None else None
			p['graph'] = copy.deepcopy(self.graph)
			p['is_clone'] = True
		else:
			p['frame'] = self.pf
			p['utility_ca'] = self.utility_ca
			p['utility_co'] = self.utility_co
			p['quantity_ca'] = self.quantity_ca
			p['quantity_scale'] = self.quantity_scale
			p['graph'] = self.graph
			p['is_clone'] = True
		return p

	def set_params(self, **kwargs):
		if 'frame' in kwargs and kwargs['frame'] is not None:
			self.frame = kwargs['frame']

		self.utility_ca = kwargs.get('utility_ca', None)
		self.utility_co = kwargs.get('utility_co', None)
		self.quantity_ca = kwargs.get('quantity_ca', None)
		self.quantity_scale = kwargs.get('quantity_scale', None)
		self.graph = kwargs.get('graph', None)


	def fit(self, X, y, sample_weight=None, **kwargs):
		"""Estimate the parameters of this model from the training set (X, y).

		Parameters
		----------
		X : pandas.DataFrame
			If given in idce format, a dataFrame with *n_casealts* rows.
		y : array-like or str
			The target choice values.  If given as a ``str``, use that named column of `X`.
		sample_weight : array-like, shape = [n_cases] or [n_casealts], or None
			Sample weights. If None, then samples are equally weighted. If shape is *n_casealts*,
			the array is collapsed to *n_cases* by taking only the first weight in each case.

		Returns
		-------
		self : object
		"""

		if not isinstance(X, pandas.DataFrame):
			raise TypeError(f'must fit on an {self._sklearn_data_format} dataframe')

		if sample_weight is not None:
			raise NotImplementedError('sample_weight not implemented')

		if self._sklearn_data_format == 'idce':

			if sample_weight is not None:
				if isinstance(sample_weight, str):
					sample_weight = X[sample_weight]
				if len(sample_weight) == X.shape[0]:
					sample_weight = sample_weight.groupby(X.index.labels[0]).first()

			if isinstance(y, str):
				y = X[y].unstack().fillna(0)
			elif isinstance(y, (pandas.DataFrame, pandas.Series)):
				y = y.unstack().fillna(0)
			else:
				y = pandas.Series(y, index=X.index).unstack().fillna(0)

			from .dataframes import _check_dataframe_of_dtype
			if _check_dataframe_of_dtype(X, l4_float_dtype):
				# when the dataframe is an array of the correct type,
				# it is efficient to use it directly
				self.dataframes = DataFrames(
					ce = X,
					ch = y,
					wt = sample_weight,
				)
			else:
				# when the dataframe is not an array of the correct type,
				# it is efficient to only manipulate needed columns
				self.dataframes = DataFrames(
					ce = X[self.required_data().ca],
					ch = y,
					wt = sample_weight,
				)
		else:
			raise NotImplementedError(self._sklearn_data_format)

		self.maximize_loglike(**kwargs)

		return self

	def predict(self, X):
		"""Predict choices for X.

		This method returns the index of the maximum probability choice, not the probability.
		To recover the probability, see :ref:`predict_proba`.

		Parameters
		----------
		X : pandas.DataFrame
			In idce format

		Returns
		-------
		y : array of shape = [n_cases]
			The predicted choices.
		"""

		return numpy.argmax(self.predict_proba(X), axis=1)

	def predict_proba(self, X):
		"""Predict probability for X.

		Parameters
		----------
		X : pandas.DataFrame
			In idce format

		Returns
		-------
		y : array of shape = [n_cases, n_alts]
			The predicted probabilities.
		"""

		if not isinstance(X, pandas.DataFrame):
			raise TypeError(f'must fit on an {self._sklearn_data_format} dataframe')

		if self._sklearn_data_format == 'idce':
			self.dataframes = DataFrames(
				ce = X[self.required_data().ca],
			)
		else:
			raise NotImplementedError(self._sklearn_data_format)

		result = self.probability(return_dataframe=self._sklearn_data_format)

		return result

	def score(self, X, y, sample_weight=None):
		"""
		Returns the mean log loss on the given test data and labels.

		Parameters
		----------
		X : pandas.DataFrame
			If given in idce format, a dataFrame with *n_casealts* rows.
		y : array-like or str
			The target choice values.  If given as a ``str``, use that named column of `X`.
		sample_weight : array-like, shape = [n_casealts], or None
			Sample weights. If None, then samples are equally weighted.

		Returns
		-------
		score : float
			Mean log loss of self.predict_proba(X) wrt. y.
		"""
		if isinstance(y, str):
			y = X[y].values.reshape(-1)
		elif isinstance(y, (pandas.DataFrame, pandas.Series)):
			y = y.values.reshape(-1)
		else:
			y = y.reshape(-1)

		pr = self.predict_proba(X)

		weight_adjust = numpy.sum(y) / self.dataframes.n_cases

		if sample_weight is not None:
			sample_weight = sample_weight[y>0] / weight_adjust

		pr = pr[y>0]
		y = y[y>0]

		if sample_weight is None:
			return -numpy.sum(numpy.log(pr) * y / weight_adjust) / self.dataframes.n_cases
		else:
			return -numpy.sum(numpy.log(pr) * y * sample_weight) / numpy.sum(sample_weight)


	def __parameter_table_section(self, pname):

		from xmle import Elem

		pname_str = str(pname)
		pf = self.pf
		# if pname in self.rename_parameters:
		# 	colspan = 0
		# 	if 'std err' in pf.columns:
		# 		colspan += 1
		# 	if 't stat' in pf.columns:
		# 		colspan += 1
		# 	if 'nullvalue' in pf.columns:
		# 		colspan += 1
		# 	return [
		# 		Elem('td', text="{:.4g}".format(pf.loc[self.rename_parameters[pname],'value'])),
		# 		Elem('td', text="= "+self.rename_parameters[pname], colspan=str(colspan)),
		# 	]
		if pf.loc[pname_str,'holdfast']:
			colspan = 0
			if 'std err' in pf.columns:
				colspan += 1
			if 't stat' in pf.columns:
				colspan += 1
			if 'nullvalue' in pf.columns:
				colspan += 1
			# if pf.loc[pname_str,'holdfast'] == holdfast_reasons.asc_but_never_chosen:
			# 	return [
			# 		Elem('td', text="{:.4g}".format(pf.loc[pname_str,'value'])),
			# 		Elem('td', text="fixed value, never chosen", colspan=str(colspan)),
			# 	]
			# elif pf.loc[pname_str, 'holdfast'] == holdfast_reasons.snap_to_constant_eq:
			# 	return [
			# 		Elem('td', text="{:.4g}".format(pf.loc[pname_str, 'value'])),
			# 		Elem('td', text="fixed value", colspan=str(colspan)),
			# 	]
			# elif pf.loc[pname_str, 'holdfast'] == holdfast_reasons.snap_to_constant_le:
			# 	return [
			# 		Elem('td', text="{:.4g}".format(pf.loc[pname_str, 'value'])),
			# 		Elem('td', text="≤ {:.4g}".format(pf.loc[pname_str, 'value']), colspan=str(colspan)),
			# 	]
			# elif pf.loc[pname_str, 'holdfast'] == holdfast_reasons.snap_to_constant_ge:
			# 	return [
			# 		Elem('td', text="{:.4g}".format(pf.loc[pname_str, 'value'])),
			# 		Elem('td', text="≥ {:.4g}".format(pf.loc[pname_str, 'value']), colspan=str(colspan)),
			# 	]
			# elif pf.loc[pname_str, 'note'] != "" and not pandas.isnull(pf.loc[pname_str, 'note']):
			# 	return [
			# 		Elem('td', text="{:.4g}".format(pf.loc[pname_str,'value'])),
			# 		Elem('td', text=pf.loc[pname_str, 'note'], colspan=str(colspan)),
			# 	]
			# else:
			return [
				Elem('td', text="{:.4g}".format(pf.loc[pname_str,'value'])),
				Elem('td', text="fixed value", colspan=str(colspan), style="text-align: left;"),
			]
		else:
			result = [ Elem('td', text="{:.4g}".format(pf.loc[pname_str,'value'])) ]
			if 'std err' in pf.columns:
				result += [ Elem('td', text="{:#.3g}".format(pf.loc[pname_str, 'std err'])), ]
			if 't stat' in pf.columns:
				result += [ Elem('td', text="{:#.2f}".format(pf.loc[pname_str, 't stat'])), ]
			if 'nullvalue' in pf.columns:
				result += [ Elem('td', text="{:#.2g}".format(pf.loc[pname_str, 'nullvalue'])), ]
			return result


	# def pfo(self):
	# 	if self.ordering is None:
	# 		return self.pf
	# 	paramset = set(self.pf.index)
	# 	out = []
	# 	import re
	# 	if self.ordering:
	# 		for category in self.ordering:
	# 			category_name = category[0]
	# 			category_params = []
	# 			for category_pattern in category[1:]:
	# 				category_params.extend(sorted(i for i in paramset if re.match(category_pattern, i) is not None))
	# 				paramset -= set(category_params)
	# 			out.append( [category_name, category_params] )
	# 	if len(paramset):
	# 		out.append( ['Other', sorted(paramset)] )
	#
	# 	tuples = []
	# 	for c,pp in out:
	# 		for p in pp:
	# 			tuples.append((c,p))
	#
	# 	ix = pandas.MultiIndex.from_tuples(tuples, names=['Category','Parameter'])
	#
	# 	f = self.pf
	# 	f = f.reindex(ix.get_level_values(1))
	# 	f.index = ix
	# 	return f

	def parameter_summary(self):
		pfo = self.pfo()

		ordered_p = list(pfo.index)

		any_colons = False
		for rownum in range(len(ordered_p)):
			if ":" in ordered_p[rownum][1]:
				any_colons = True
				break

		from xmle import ElemTable

		div = ElemTable('div')
		table = div.put('table')

		thead = table.put('thead')
		tr = thead.put('tr')
		tr.put('th', text='Category', style="text-align: left;")
		if any_colons:
			tr.put('th', text='Parameter', colspan='2', style="text-align: left;")
		else:
			tr.put('th', text='Parameter', style="text-align: left;")

		tr.put('th', text='Value')
		if 'std err' in pfo.columns:
			tr.put('th', text='Std Err')
		if 't stat' in pfo.columns:
			tr.put('th', text='t Stat')
		if 'nullvalue' in pfo.columns:
			tr.put('th', text='Null Value')

		tbody = table.put('tbody')

		swallow_categories = 0
		swallow_subcategories = 0

		for rownum in range(len(ordered_p)):
			tr = tbody.put('tr')
			if swallow_categories > 0:
				swallow_categories -= 1
			else:
				nextrow = rownum + 1
				while nextrow<len(ordered_p) and ordered_p[nextrow][0] == ordered_p[rownum][0]:
					nextrow += 1
				swallow_categories = nextrow - rownum - 1
				if swallow_categories:
					tr.put('th', text=ordered_p[rownum][0], rowspan=str(swallow_categories+1), style="vertical-align: top; text-align: left;")
				else:
					tr.put('th', text=ordered_p[rownum][0], style="vertical-align: top; text-align: left;")
			parameter_name = ordered_p[rownum][1]
			if ":" in parameter_name:
				parameter_name = parameter_name.split(":",1)
				if swallow_subcategories > 0:
					swallow_subcategories -= 1
				else:
					nextrow = rownum + 1
					while nextrow < len(ordered_p) and ":" in ordered_p[nextrow][1] and ordered_p[nextrow][1].split(":",1)[0] == parameter_name[0]:
						nextrow += 1
					swallow_subcategories = nextrow - rownum - 1
					if swallow_subcategories:
						tr.put('th', text=parameter_name[0], rowspan=str(swallow_subcategories+1), style="vertical-align: top; text-align: left;")
					else:
						tr.put('th', text=parameter_name[0], style="vertical-align: top; text-align: left;")
				tr.put('th', text=parameter_name[1], style="vertical-align: top; text-align: left;")
			else:
				if any_colons:
					tr.put('th', text=parameter_name, colspan="2", style="vertical-align: top; text-align: left;")
				else:
					tr.put('th', text=parameter_name, style="vertical-align: top; text-align: left;")
			tr << self.__parameter_table_section(ordered_p[rownum][1])

		return div
