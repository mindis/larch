
import setup_common
from distutils.ccompiler import new_compiler
import os, platform, distutils

def build_apsw():

	name = "apsw"
	source = 'sqlite/apsw/apsw.c'
	exports = ['_PyInit_apsw',]
	compiler_pre_args = ['-arch', 'i386', '-arch', 'x86_64']
	linker_pre_args = ['-arch', 'i386', '-arch', 'x86_64']
	linker_post_args = []
	
	libdir = setup_common.shlib_folder()
	pylibdir = '/Library/Frameworks/Python.framework/Versions/3.5/lib'
	
	print("building",name,"...")

	# Create compiler with default options
	c = new_compiler()
	c.add_include_dir("./sqlite")
	c.add_include_dir(distutils.sysconfig.get_python_inc())
	c.define_macro("EXPERIMENTAL","1")
	output_file = c.shared_object_filename(name)
	print(output_file)

	try:
		need_to_update = (os.path.getmtime(source) > os.path.getmtime(os.path.join(libdir, output_file)))
	except:
		need_to_update = True

	# change dynamic library install name
	if platform.system() == 'Darwin':
		linker_post_args += ['-install_name', '@loader_path/{}'.format(output_file)]

	if need_to_update:
		# Compile into .o files
		objects = c.compile([source], extra_preargs=compiler_pre_args, output_dir=setup_common.temp_folder())
		# Create shared library
		c.link_shared_object(objects, output_file, output_dir=libdir, export_symbols=exports, 
				 				libraries=['larchsqlite','python3.5'], library_dirs=[libdir, pylibdir],
								extra_preargs=linker_pre_args, extra_postargs=linker_post_args)
	else:
		print("apparently no need to update",name," at ",os.path.join(libdir, output_file))

	


# 	apsw = Extension('larch.apsw',
# 				 ['sqlite/apsw/apsw.c',],
# 				 libraries=['larchsqlite', ],
# 				 library_dirs=[shlib_folder(),],
# 				 define_macros=local_macros,
# 				 include_dirs= [ './sqlite', './sqlite/apsw', ],
# 				 extra_compile_args=local_apsw_compile_args,
# #				 extra_link_args=apsw_extra_link_args,
# 				 )
		
		
if __name__=="__main__":
	try:
		build_apsw()
	except:
		exit(-1)
	exit(0)