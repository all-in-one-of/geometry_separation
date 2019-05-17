import hou


def create_subnet(object_name):
	subnet_node = hou.node('/obj').createNode('subnet', '{0}_split_geometry'.format(object_name))
	subnet_node.moveToGoodPosition()
	return subnet_node

def create_split_into_parts_node(parent_node):
	split_into_parts_node = parent_node.createNode('geo', 'split_into_parts')
	split_into_parts_node.moveToGoodPosition()
	return split_into_parts_node

def create_merge_node(parent_node, alembic_file, object_name):
	merge_node = parent_node.createNode('object_merge', 'get_{0}_geometry'.format(object_name))
	merge_node.moveToGoodPosition()
	merge_node.parm('objpath1').set(alembic_file)
	return merge_node

def create_blast_node(parent_node, input_node, output_collection):
	node_dict = {}
	main_unique_lst = output_collection[0]
	main_split_path_lst = output_collection[1]
	main_split_shape_lst = output_collection[2]

	for main_path in main_split_path_lst:
		null_node_list = []
		null_node_dict = {}
		split_name = main_path.split('/')[1]
		blast_node = parent_node.createNode('blast', 'isolate_{0}'.format(split_name))
		blast_node.setInput(0, input_node)
		blast_node.moveToGoodPosition(move_inputs = False)
		blast_node.setParms({'grouptype':4, 'negate':1, 'group':'@path={0}'.format(main_path)})
		for main_shape in main_split_shape_lst:
			if main_shape.startswith(main_path):
				sub_blast_node = parent_node.createNode('blast')
				sub_blast_node.setInput(0, blast_node)
				sub_blast_node.moveToGoodPosition(move_inputs = False)
				sub_blast_node.setParms({'grouptype':4, 'negate':1, 'group':'@path={0}'.format(main_shape)})
				null_node = parent_node.createNode('null','OUT_{0}_part_1'.format(split_name))
				null_node.setInput(0, sub_blast_node)
				null_node.moveToGoodPosition(move_inputs=0)
				null_node_list.append(null_node)
			null_node_dict = {main_path : null_node_list}
		node_dict.update(null_node_dict)
	return node_dict

def create_unpack(parent_node, input_node):
	unpack_node = parent_node.createNode('unpack')
	unpack_node.setInput(0, input_node)
	unpack_node.moveToGoodPosition(move_inputs=False)
	unpack_node.setParms({'transfer_attributes':'path'})
	convert_node = parent_node.createNode('convert')
	convert_node.setInput(0, unpack_node)
	convert_node.moveToGoodPosition(move_inputs=False)
	return convert_node

def construct_paths(parent_node, input_node, main_grp_name):

	name_index = 0
	main_unique_lst = []
	main_split_path_lst = []
	main_split_shape_lst = []
	output_collection = []

	geo = input_node.geometry()
	for prim in geo.prims():
		path = prim.attribValue('path')
		path_lst = path.split('/')
		if main_grp_name in path_lst:
			name_index = path_lst.index(main_grp_name)
		if path_lst[name_index] not in main_unique_lst:
			main_unique_lst.append(path_lst[name_index]) # get main_unique_lst

		if path.find(path_lst[name_index]) and path.find(path_lst[-1]):
			main_split_path = '*/' + path_lst[name_index] + '/*'
			main_split_shape = main_split_path + path_lst[-1]
			if main_split_path not in main_split_path_lst:
				main_split_path_lst.append(main_split_path)
			if main_split_shape not in main_split_shape_lst:
				main_split_shape_lst.append(main_split_shape) # get main_split_shape_lst and path_lst
	output_collection = [main_unique_lst, main_split_path_lst, main_split_shape_lst]

	return output_collection

def split_into_parts(parent_node,alembic_file, object_name, main_grp_name, unpack_before_split):
	outputs = []
	merge_node = create_merge_node(parent_node, alembic_file, object_name)
	next_input = merge_node
	if unpack_before_split:
		next_input = create_unpack(parent_node, next_input)
	output_collection = construct_paths(parent_node, next_input, main_grp_name)
	node_dict = create_blast_node(parent_node, next_input,output_collection)
	outputs = [node_dict, output_collection]
	return outputs



def create_shading_geo(parent_node, input_node, outputs, object_name):
	null_node_lst = []
	node_dict = outputs[0]
	geo_nodes = node_dict.keys()
	shape_node_lst = node_dict.values()
	for node in geo_nodes:
		split_name = node.split('/')[1]
		shading_geo = parent_node.createNode('geo', '{0}_{1}_shading_geo'.format(object_name, split_name))
		shading_geo.setInput(0, input_node)
		shading_geo.moveToGoodPosition(move_inputs=False)
		merge_node = shading_geo.createNode('merge')
		for shape_node in node_dict.get(node):
			object_merge = shading_geo.createNode('object_merge')
			object_merge.parm('objpath1').set(shape_node.path())
			object_merge.moveToGoodPosition(move_inputs=False)
			mat_node = shading_geo.createNode('material')
			mat_node.setInput(0,object_merge)
			mat_node.moveToGoodPosition(move_inputs=False)
			merge_node.setNextInput(mat_node,0)
			merge_node.moveToGoodPosition(move_inputs=False)
		null_node = shading_geo.createNode('null','OUT_{0}_shading'.format(split_name))
		null_node.setInput(0, merge_node)
		null_node.moveToGoodPosition(move_inputs=False)
		null_node.setDisplayFlag(True)
		null_node.setRenderFlag(True)
		null_node_lst.append(null_node)
	return null_node_lst

def extract(alembic_file, object_name, main_grp_name, unpack_before_split):
	subnet = create_subnet(object_name)
	split_geo_node = create_split_into_parts_node(subnet)
	outputs = split_into_parts(split_geo_node, alembic_file, object_name, main_grp_name, unpack_before_split)
	out_nodes_lst = create_shading_geo(subnet, split_geo_node, outputs, object_name)