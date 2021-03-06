import networkx as nx
from collections import OrderedDict
import numpy
from ..util.touch_notifier import TouchNotify
from ..util.lazy import lazy

class NestingTree(TouchNotify,nx.DiGraph):

	node_dict_factory = OrderedDict
	adjlist_dict_factory = OrderedDict

	def __init__(self, *arg, root_id=0, suggested_elemental_order=(), **kwarg):
		if len(arg) and isinstance(arg[0], NestingTree):
			super().__init__(*arg, **kwarg)
			self._root_id = arg[0]._root_id
			if suggested_elemental_order != ():
				self._suggested_elemental_order = suggested_elemental_order
			else:
				self._suggested_elemental_order = arg[0]._suggested_elemental_order
		else:
			super().__init__(*arg, **kwarg)
			self._root_id = root_id
			self._suggested_elemental_order = suggested_elemental_order
		if self._root_id not in self.node:
			self.add_node(root_id, name='_root_', root=True)
		self._clear_caches()

	def __eq__(self, other):
		return (
			self._adj == other._adj and
			self._node == other._node and
			self._root_id == other._root_id and
			self._suggested_elemental_order == other._suggested_elemental_order
		)

	def suggest_elemental_order(self, order):
		self._suggested_elemental_order = tuple(order)

	@property
	def root_id(self):
		return self._root_id

	def _clear_caches(self):
		NestingTree.topological_sorted.invalidate(self, 'topological_sorted')
		NestingTree.topological_sorted_no_elementals.invalidate(self, 'topological_sorted_no_elementals')
		NestingTree.standard_sort.invalidate(self, 'standard_sort')
		NestingTree.standard_sort.invalidate(self, 'standard_slot_map')
		NestingTree.elementals.invalidate(self, 'elementals')
		NestingTree.standard_competitive_edge_list.invalidate(self, 'standard_competitive_edge_list')
		NestingTree.standard_competitive_edge_list_2.invalidate(self, 'standard_competitive_edge_list_2')
		self._predecessor_slots = {}
		self._successor_slots = {}
		self.touch()

	def add_edge(self, u, v, *arg, **kwarg):
		if 'implied' not in kwarg:
			drops = []
			for u_,v_,imp_ in self.in_edges(nbunch=[v], data='implied'):
				if imp_:
					drops.append([u_,v_])
			for d in drops:
				self._remove_edge_no_implied(*d)
		self._clear_caches()
		return super().add_edge(u, v, *arg, **kwarg)

	def _remove_edge_no_implied(self, u, v, *arg, **kwarg):
		result = super().remove_edge(u, v)
		self._clear_caches()
		return result

	def remove_edge(self, u, v, *arg, **kwarg):
		result = super().remove_edge(u, v)
		if self.in_degree(v)==0 and v!=self._root_id:
			self.add_edge(self._root_id, v, implied=True)
		self._clear_caches()
		return result

	def add_node(self, code, *arg, children=(), parent=None, parents=None, phi_parameters=None, **kwarg):
		if parents is not None and parent is not None:
			raise TypeError("cannot give both parent and parents arguments")
		super().add_node(code, *arg, **kwarg)
		for child in children:
			self.add_edge(code, child)
		if parent is not None:
			self.add_edge(parent, code)
		elif parents is not None:
			for p in parents:
				self.add_edge(p, code)
		else:
			if self.in_degree(code)==0 and code!=self._root_id:
				self.add_edge(self._root_id, code, implied=True)
		if phi_parameters is not None:
			for k, parametername in phi_parameters.items():
				if (code, k) in self.edges:
					self.edges[code, k]['parameter'] = str(parametername)
				elif (k,code) in self.edges:
					self.edges[k, code]['parameter'] = str(parametername)
				else:
					raise ValueError(f"connected node {k} from phi_parameters not found")
		self._clear_caches()

	def new_node(self, *arg, **kwarg):
		proposed_code = len(self)
		while proposed_code in self:
			proposed_code += 1
		self.add_node(proposed_code, *arg, **kwarg)
		return proposed_code

	def add_nodes(self, codes, *arg, parent=None, **kwarg):
		for code in codes:
			self.add_node(code, *arg, parent=parent, **kwarg)

	@lazy
	def topological_sorted(self):
		return list(reversed(list(nx.topological_sort(self))))

	@lazy
	def topological_sorted_no_elementals(self):
		# if self._topological_sorted_no_elementals is not None:
		# 	# use cached  if available
		# 	return self._topological_sorted_no_elementals
		# self._topological_sorted_no_elementals = self.topological_sorted.copy()
		# for code, out_degree in self.out_degree:
		# 	if not out_degree:
		# 		self._topological_sorted_no_elementals.remove(code)
		# return self._topological_sorted_no_elementals
		result = self.topological_sorted.copy()
		for code, out_degree in self.out_degree:
			if not out_degree:
				result.remove(code)
		return result

	@lazy
	def standard_sort(self):
		return self.elementals + tuple(self.topological_sorted_no_elementals)

	def node_name(self, code):
		return self.node[code].get('name', str(code))

	@property
	def standard_sort_names(self):
		return [self.node_name(s) for s in self.standard_sort]

	def node_names(self):
		return {s:(self.node_name(s) or s) for s in self.standard_sort}

	@lazy
	def standard_slot_map(self):
		return {i:n for n,i in enumerate(self.standard_sort)}

	def predecessor_slots(self, code):
		if code in self._predecessor_slots:
			return self._predecessor_slots[code]
		s = numpy.empty(self.in_degree(code), dtype=numpy.int32)
		for n,i in enumerate( self.predecessors(code) ):
			s[n] = self.standard_slot_map[i]
		self._predecessor_slots[code] = s
		return s

	def successor_slots(self, code):
		if code in self._successor_slots:
			return self._successor_slots[code]
		s = numpy.empty(self.out_degree(code), dtype=numpy.int32)
		for n,i in enumerate( self.successors(code) ):
			s[n] = self.standard_slot_map[i]
		self._successor_slots[code] = s
		return s

	def __elementals_iter(self):
		for code, out_degree in self.out_degree:
			if not out_degree:
				yield code

	@lazy
	def elementals(self):
		result = []
		found = set()
		for e in self._suggested_elemental_order:
			if self.out_degree(e)==0:
				result.append(e)
				found.add(e)
		for e in sorted(self.__elementals_iter()):
			if e not in found:
				result.append(e)
				found.add(e)
		return tuple(result)

	def n_elementals(self):
		return len(self.elementals)

	def n_intermediate_nests(self):
		return len(self.nodes) - self.n_elementals() - 1

	def elemental_descendants_iter(self, code):
		if not self.out_degree(code):
			yield code
			return
		all_d = nx.descendants(self, code)
		for dcode, dout_degree in self.out_degree(all_d):
			if not dout_degree:
				yield dcode

	def elemental_descendants(self, code):
		return [i for i in self.elemental_descendants_iter(code)]

	@property
	def n_edges(self):
		return self.number_of_edges()

	def edge_slot_arrays(self, alpha_locator=None):
		s = self.n_edges
		up = numpy.zeros(s, dtype=numpy.int32)
		dn = numpy.zeros(s, dtype=numpy.int32)
		first_visit = numpy.zeros(s, dtype=numpy.int32)
		alloc_slot = numpy.full_like(first_visit, -1)
		n = s
		first_visit_found = set()
		for upcode in reversed(self.standard_sort):
			upslot = self.standard_slot_map[upcode]
			for dnslot in reversed(self.successor_slots(upcode)):
				n -= 1
				up[n] = upslot
				dn[n] = dnslot
		for n in range(s):
			if dn[n] not in first_visit_found:
				first_visit[n] = 1
				first_visit_found.add(dn[n])
		if alpha_locator is not None:
			for n in range(s):
				alloc_slot[n] = alpha_locator.get( (self.standard_sort[up[n]], self.standard_sort[dn[n]]), -1 )
		return up, dn, first_visit, alloc_slot

	def nodes_with_successors_iter(self):
		for code, out_degree in self.out_degree:
			if out_degree:
				yield code

	def nodes_with_multiple_predecessors_iter(self):
		for code, in_degree in self.in_degree:
			if in_degree>1:
				yield code

	@lazy
	def standard_competitive_edge_list(self):
		alphas = []
		for n in self.nodes_with_multiple_predecessors_iter():
			predecessors = sorted(self.predecessors(n))
			for k in predecessors:
				alphas.append( (k,n) )
		return alphas

	@lazy
	def standard_competitive_edge_list_2(self):
		alphas = []
		for n in self.nodes_with_multiple_predecessors_iter():
			predecessors = sorted(self.predecessors(n))
			alphas.append( (predecessors, n) )
		return alphas


	def __getstate__(self):
		attr = {} # self.__dict__.copy()
		no_pickle = (
			'topological_sorted',
			'topological_sorted_no_elementals',
			'standard_sort',
			'standard_slot_map',
			#'_standard_elemental_sort',
			'elementals',
			'_predecessor_slots',
			'_successor_slots',
			'_TouchNotify__touch_callback',
			'node_dict_factory',

		)
		for k,v in self.__dict__.items():
			if k not in no_pickle:
				attr[k] = v
		return attr

	def __setstate__(self, state):
		self.__dict__ = state.copy()

	def __xml__(self, **format):
		viz = None
		dot = None
		try:
			import pygraphviz as viz
		except ImportError:
			try:
				import pydot as dot
			except ImportError:
				pass

		if viz is None and dot is None:
			import warnings
			warnings.warn("pygraphviz module not installed, unable to draw nesting tree")
			raise NotImplementedError("pygraphviz module not installed, unable to draw nesting tree")

		if viz is not None:
			existing_format_keys = list(format.keys())
			for key in existing_format_keys:
				if key.upper()!=key: format[key.upper()] = format[key]
			if 'SUPPRESSGRAPHSIZE' not in format:
				if 'GRAPHWIDTH' not in format: format['GRAPHWIDTH'] = 6.5
				if 'GRAPHHEIGHT' not in format: format['GRAPHHEIGHT'] = 4
			if 'UNAVAILABLE' not in format: format['UNAVAILABLE'] = True
			# x = XML_Builder("div", {'class':"nesting_graph larch_art"})
			# x.h2("Nesting Structure", anchor=1, attrib={'class':'larch_art_xhtml'})
			from io import BytesIO
			if 'SUPPRESSGRAPHSIZE' not in format:
				G=viz.AGraph(name='Tree',directed=True,size="{GRAPHWIDTH},{GRAPHHEIGHT}".format(**format))
			else:
				G=viz.AGraph(name='Tree',directed=True)
			for n in self.nodes:
				nname = self.nodes[n].get('name', n)
				if nname == n:
					G.add_node(n, label='<{1}>'.format(n,nname), style='rounded,solid', shape='box')
				else:
					G.add_node(n, label='<{1} <FONT COLOR="#999999">({0})</FONT>>'.format(n,nname), style='rounded,solid', shape='box')
			eG = G.add_subgraph(name='cluster_elemental', nbunch=self.elementals, color='#cccccc', bgcolor='#eeeeee',
						   label='Elemental Alternatives', labelloc='b', style='rounded,solid')
			unavailable_nodes = set()
			# if format['UNAVAILABLE']:
			# 	if self.is_provisioned():
			# 		try:
			# 			for n, ncode in enumerate(self.alternative_codes()):
			# 				if numpy.sum(self.Data('Avail'),axis=0)[n,0]==0: unavailable_nodes.add(ncode)
			# 		except: raise
			# 	try:
			# 		legible_avail = not isinstance(self.df.queries.avail, str)
			# 	except:
			# 		legible_avail = False
			# 	if legible_avail:
			# 		for ncode,navail in self.df.queries.avail.items():
			# 			try:
			# 				if navail=='0': unavailable_nodes.add(ncode)
			# 			except: raise
			# 	eG.add_subgraph(name='cluster_elemental_unavailable', nbunch=unavailable_nodes, color='#bbbbbb', bgcolor='#dddddd',
			# 				   label='Unavailable Alternatives', labelloc='b', style='rounded,solid')
			G.add_node(self.root_id, label="Root")
			up_nodes = set()
			down_nodes = set()
			for i,j in self.edges:
				G.add_edge(i,j)
				down_nodes.add(j)
				up_nodes.add(i)
			pyg_imgdata = BytesIO()
			try:
				G.draw(pyg_imgdata, format='svg', prog='dot')       # write postscript in k5.ps with neato layout
			except ValueError as err:
				if 'in path' in str(err):
					import warnings
					warnings.warn(str(err)+"; unable to draw nesting tree in report")
					raise NotImplementedError()
			import xml.etree.ElementTree as ET
			ET.register_namespace("","http://www.w3.org/2000/svg")
			ET.register_namespace("xlink","http://www.w3.org/1999/xlink")
			return ET.fromstring(pyg_imgdata.getvalue().decode())
		else:

			N = self
			pydot = dot

			# set Graphviz graph type
			if N.is_directed():
				graph_type = 'digraph'
			else:
				graph_type = 'graph'
			strict = nx.number_of_selfloops(N) == 0 and not N.is_multigraph()

			name = N.name
			graph_defaults = N.graph.get('graph', {})
			if name is '':
				P = pydot.Dot('', graph_type=graph_type, strict=strict,
							  **graph_defaults)
			else:
				P = pydot.Dot('"%s"' % name, graph_type=graph_type, strict=strict,
							  **graph_defaults)
			try:
				P.set_node_defaults(**N.graph['node'])
			except KeyError:
				pass
			try:
				P.set_edge_defaults(**N.graph['edge'])
			except KeyError:
				pass

			for n, nodedata in N.nodes(data=True):
				str_nodedata = dict((k if k!='name' else 'name_', str(v)) for k, v in nodedata.items())
				p = pydot.Node(str(n), **str_nodedata)
				P.add_node(p)

			if N.is_multigraph():
				for u, v, key, edgedata in N.edges(data=True, keys=True):
					str_edgedata = dict((k, str(v)) for k, v in edgedata.items()
										if k != 'key')
					edge = pydot.Edge(str(u), str(v),
									  key=str(key), **str_edgedata)
					P.add_edge(edge)

			else:
				for u, v, edgedata in N.edges(data=True):
					str_edgedata = dict((k, str(v)) for k, v in edgedata.items())
					edge = pydot.Edge(str(u), str(v), **str_edgedata)
					P.add_edge(edge)

			###
			from xmle import Elem
			return Elem.from_any(P.create_svg())

	def _repr_html_(self):
		from xmle import Elem
		x = Elem('div') << (self.__xml__())
		return x.tostring()

	def partial_figure(self, including_nodes=None, source=None, *, n=None, n_at_level=3, n_expand=1):
		"""
		Generate a partial figure of the graph.

		Parameters
		----------
		including_nodes : iterable or None
			An iterable containing node codes or names (or a mix).
		source : nodecode, optional
			All paths from this node to everything in `including_nodes` will be represented.
			Defaults to `root_id`.
		n : int
			If including_nodes is None, select this number of nodes randomly

		Returns
		-------
		Elem
		"""
		if source is None:
			source = self.root_id
		from networkx.algorithms.simple_paths import all_simple_paths
		shows = set()

		if including_nodes is None and n is not None:
			including_nodes = sorted(numpy.random.choice(self.nodes, n, replace=False))

		if including_nodes is None and n_at_level is not None:
			from collections import deque
			import itertools
			q = deque([self.root_id])
			including_nodes = []
			while q:
				i = q.popleft()
				take = tuple(itertools.islice(self.successors(i), n_at_level))
				q.extend(take[:n_expand])
				including_nodes.extend(take)

		# Add every node in every path from the root to each `including_nodes`
		for each_node in including_nodes:
			if each_node in self.node:
				for i in all_simple_paths(self, source, each_node):
					for j in i:
						shows.add(j)
			else:
				for each_node_ in self.get_nodes_by_name(each_node):
					for i in all_simple_paths(self, source, each_node_):
						for j in i:
							shows.add(j)
		s = self.subgraph(shows)
		return graph_to_figure(s)

	def get_nodes_by_name(self, name):
		result = [k for k,v in self.nodes(data=True) if v.get('name')==name]
		return result

	def subgraph_from(self, node):
		from collections import deque
		Q = deque([node])
		found = set()
		while len(Q):
			i = Q.popleft()
			if i not in found:
				found.add(i)
				Q.extend(self.successors(i))
		return NestingTree(self.subgraph(found), root_id=node)

	def stats_summarize(self):
		print("Graph Stats")
		print(f"  Overall: {len(self)} nodes")
		tier = [self.root_id]
		next_tier = list(self.successors(self.root_id))
		n = 0
		while len(next_tier):
			tier = next_tier
			n += 1
			print(f"   Tier {n}: {len(tier)} nodes")
			next_tier = list()
			for i in tier:
				next_tier.extend(self.successors(i))

	def _get_simple_mu_and_alpha(self, model):
		alpha = numpy.zeros([len(self), len(self)], dtype=numpy.float64)
		mu    = numpy.ones ([len(self),          ], dtype=numpy.float64)
		muslots= numpy.full([len(self),          ], -1, dtype=numpy.int32)
		for child, childcode in enumerate(self.standard_sort):
			for parent in self.predecessor_slots(childcode):
				alpha[parent, child] = 1
			pname = self.nodes[childcode].get('parameter', None)
			mu[child] = model.get_value_x(pname, 1.0)
			muslots[child] = model.get_slot_x(pname, True)

		s = self.n_edges
		up = numpy.zeros(s, dtype=numpy.int32)
		dn = numpy.zeros(s, dtype=numpy.int32)
		val = numpy.zeros(s, dtype=numpy.float64)
		num = numpy.zeros(len(self.nodes), dtype=numpy.int32)
		start = numpy.full(len(self.nodes), -1, dtype=numpy.int32)
		#first_visit = numpy.zeros(s, dtype=numpy.int32)
		n = s
		#first_visit_found = set()
		for upcode in reversed(self.standard_sort):
			upslot = self.standard_slot_map[upcode]
			for dnslot in reversed(self.successor_slots(upcode)):
				n -= 1
				up[n] = upslot
				dn[n] = dnslot
				num[upslot] += 1
				start[upslot] = n
				val[n] = 1/len(self.predecessor_slots(self.standard_sort[dnslot])) # TODO make not always constant fraction
		# for n in range(s):
		# 	if dn[n] not in first_visit_found:
		# 		first_visit[n] = 1
		# 		first_visit_found.add(dn[n])

		return mu, muslots, alpha, up, dn, num, start, val

def graph_to_figure(graph, **format):

	try:
		import pygraphviz as viz
	except ImportError:
		import warnings
		warnings.warn("pygraphviz module not installed, unable to draw nesting tree")
		raise NotImplementedError("pygraphviz module not installed, unable to draw nesting tree")
	existing_format_keys = list(format.keys())
	for key in existing_format_keys:
		if key.upper()!=key: format[key.upper()] = format[key]
	if 'SUPPRESSGRAPHSIZE' not in format:
		if 'GRAPHWIDTH' not in format: format['GRAPHWIDTH'] = 6.5
		if 'GRAPHHEIGHT' not in format: format['GRAPHHEIGHT'] = 4
	if 'UNAVAILABLE' not in format: format['UNAVAILABLE'] = True
	# x = XML_Builder("div", {'class':"nesting_graph larch_art"})
	# x.h2("Nesting Structure", anchor=1, attrib={'class':'larch_art_xhtml'})
	from io import BytesIO
	if 'SUPPRESSGRAPHSIZE' not in format:
		G=viz.AGraph(name='Tree',directed=True,size="{GRAPHWIDTH},{GRAPHHEIGHT}".format(**format))
	else:
		G=viz.AGraph(name='Tree',directed=True)
	for n in graph.nodes:
		nname = graph.nodes[n].get('name', n)
		if nname == n:
			G.add_node(n, label='<{1}>'.format(n,nname), style='rounded,solid', shape='box')
		else:
			G.add_node(n, label='<{1} <FONT COLOR="#999999">({0})</FONT>>'.format(n,nname), style='rounded,solid', shape='box')
	try:
		graph.elementals
	except AttributeError:
		pass
	else:
		eG = G.add_subgraph(name='cluster_elemental', nbunch=graph.elementals, color='#cccccc', bgcolor='#eeeeee',
					   label='Elemental Alternatives', labelloc='b', style='rounded,solid')
	unavailable_nodes = set()
	# if format['UNAVAILABLE']:
	# 	if self.is_provisioned():
	# 		try:
	# 			for n, ncode in enumerate(self.alternative_codes()):
	# 				if numpy.sum(self.Data('Avail'),axis=0)[n,0]==0: unavailable_nodes.add(ncode)
	# 		except: raise
	# 	try:
	# 		legible_avail = not isinstance(self.df.queries.avail, str)
	# 	except:
	# 		legible_avail = False
	# 	if legible_avail:
	# 		for ncode,navail in self.df.queries.avail.items():
	# 			try:
	# 				if navail=='0': unavailable_nodes.add(ncode)
	# 			except: raise
	# 	eG.add_subgraph(name='cluster_elemental_unavailable', nbunch=unavailable_nodes, color='#bbbbbb', bgcolor='#dddddd',
	# 				   label='Unavailable Alternatives', labelloc='b', style='rounded,solid')
	try:
		G.add_node(graph.root_id, label="Root")
	except AttributeError:
		pass
	up_nodes = set()
	down_nodes = set()
	for i,j in graph.edges:
		G.add_edge(i,j)
		down_nodes.add(j)
		up_nodes.add(i)
	pyg_imgdata = BytesIO()
	try:
		G.draw(pyg_imgdata, format='svg', prog='dot')       # write postscript in k5.ps with neato layout
	except ValueError as err:
		if 'in path' in str(err):
			import warnings
			warnings.warn(str(err)+"; unable to draw nesting tree in report")
			raise NotImplementedError()
	import xml.etree.ElementTree as ET
	ET.register_namespace("","http://www.w3.org/2000/svg")
	ET.register_namespace("xlink","http://www.w3.org/1999/xlink")
	result = ET.fromstring(pyg_imgdata.getvalue().decode())

	from xmle import Elem
	x = Elem('div') << result
	return x


