from simp import *
from simp import rule_compiler_tools


initialize(size=[100,200])


a = Signal(SmallUInt(2))
b = Signal(SmallUInt(2))
c = Signal(SmallUInt(2))

# --------------------------------
def test_strobe():
    print a
    b = 2
    c._ = c
    c[-1,1/2.]._ = 1

def test_strobe():
#    b = 2
    c._ = c
    c[-1,1]._ = 1
    if b==1: c._ = 2; a._ = 1
    
    


rs = rule_compiler_tools.RuleStrober(test_strobe,[test_strobe.func_globals])

for key in  rs.output_proxies.keys():
    print key,":",rs.output_proxies[key]

for key in  rs.input_proxies.keys():
    print key,":",rs.input_proxies[key]

signal_names = {repr(a): "a",repr(b):"b",repr(c):"c",repr(c[-1,1]):"c[-1,1]"}

print "-------------------------------- Inputs"

print rs.inputs()
print map(lambda x: signal_names[repr(x)],rs.inputs())

print "-------------------------------- Outputs"
print rs.outputs()
print map(lambda x: signal_names[repr(x)],rs.outputs())
print rs.tree
print rs((1,2),[None]*3)
print rs((3,1),[None]*3)



# # -------------------------------- 
# 
# a = 1
# def test_strobe():
#     print a
#     b = 2
#     c._ = c
#     c[-1,1/2.]._ = 1
# 
# a = [1,1,1]
# 
# def test_strobe():
#     print a[0:1]
# 
# try:
#     rule_compiler_tools.RuleStrober(test_strobe)
#     raise Exception, "Didn't catch the missing name"
# except NameError: pass
# 
# 
# rs = rule_compiler_tools.RuleStrober(test_strobe,[globals()])
# 
# from compiler import misc, pycodegen, ast
# 
# tree =ast.Module("",ast.Stmt([rs.tree]))
# misc.set_filename("__none__",tree)
# gen = pycodegen.ModuleCodeGenerator(tree)
# code = gen.getCode()
# mod = {}
# eval(code,mod)
# print mod.keys()
# mod["test_strobe"]()
# # -------------------------------- 
