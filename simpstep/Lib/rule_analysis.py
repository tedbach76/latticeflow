# Copyright (C) 2004,2005  Ted Bach
# License: LGPL
#    execute 'python -c "import simp; print simp.__license__"' and
#    see /LICENSE.txt in the source distribution for details
#
# CVS Info:
#   $Revision: 1.2 $
#   $Source: /u/tbach/simpstep_cvs/simp/Lib/rule_analysis.py,v $

"""
Strobe the definitions of a function---and the functions that it calls
that were defined in the same namespace.
"""


import inspect, compiler
import copy
from compiler import ast,pycodegen,misc
from compiler.ast import *
import types, string

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# SET functions
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def set_intersection(set1, set2):
    """Return the intersection of two sets. 
    Sets are represented by dictionaries and elements by keys. Values
    are insignificant."""
    out_set = {}
    for key in set1.keys():
        if set2.has_key(key):
            out_set[key] = 0
    return out_set

def set_disjoint(set1, set2): # 
    """Return the set1-set2, the disjoint of two sets. 
    Sets are represented by dictionaries and elements by keys. Values
    are insignificant."""
    out_set = {}
    for key in set1.keys():
        if not set2.has_key(key):
            out_set[key] = 0
    return out_set

def make_set(lst):
    """Convert a list to a set represented by a dictionary"""
    out_set = {}
    for x in lst: out_set[x] = 0
    return out_set

def maplisttodict(elementlist,valuedict):
    """Map an elementlist to a new dictionary with keys from the list and
    elements from dict"""
    out_dict = {}
    for x in elementlist: out_dict[x] = valuedict[x]
    return out_dict


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#        Special Visitor Classes
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

class PostorderVisitor:
    """Visit the nodes in postorder"""
    VERBOSE = 0
    DEBUG = 1
    def __init__(self):
        self.node = None

    def visit(self,node):
        pass

    def walk(s,tree): s.postorder(tree)
    
    def postorder(s, tree):
        """Do postorder walk of tree---use a recursive function.  This
        will probably be ok for most cases, since the recursion limit is 1000.
        """
        s.node_stack = []
        s.indx_stack = []
        indx = 0; nodes = [tree]
        while 1:
          if indx<len(nodes): # enqueue
              child_nodes = nodes[indx].getChildNodes()
              s.node_stack.append(nodes); s.indx_stack.append(indx)
              nodes = child_nodes
              indx = 0
          else: # pop and visit
              if len(s.node_stack) == 0: break
              nodes = s.node_stack.pop(); indx = s.indx_stack.pop()
              s.__visit__(nodes[indx]); indx+=1

    def parent(self):
        """During a visit, returns the parent of the current node"""
        return self.node_stack[-1][self.indx_stack[-1]]
        
    def replace(self,node):
        """Replace the current node with node.
        caveat: should not try to replace the top level node..."""
        parent = self.parent()
        for name in dir(parent):
            value = getattr(parent,name)            
            if isinstance(value,types.ListType):
              for i in xrange(len(value)):
                if id(value[i])==id(self.current_node):
                    value[i] = node
                    return
#            if isinstance(value,types.TupleType):
#              for i in xrange(len(value)):
#                if id(value[i])==id(self.current_node):
#                    value = list(value)
#                    value[i] = node
#                    setattr(parent,name,tuple(value))
#                    return
            else:
              if id(value)==id(self.current_node):
                  setattr(parent,name,node)
                  return
        # Handle comparison operations in a special way...
        # the problem is that they contain lists of tuples.
        # ie a==child -> Compare(Name("a"),[("==",Name("child"))])
        if isinstance(parent,ast.Compare):
            for i in xrange(len(parent.ops)):
                op,value = parent.ops[i]
                if id(value)==id(self.current_node):
                    parent.ops[i] = (op,node)
                    return
        # same problem for an if statement block
        elif isinstance(parent,ast.If):
            for i in xrange(len(parent.tests)):
                test,do = parent.tests[i]
                if id(test)==id(self.current_node):
                    parent.tests[i] = (node,do)
                    return

        if self.DEBUG: 
          raise Exception, "Unable to replace %s in %s " % (node,parent)
              
    def __visit__(self,node):
        self.current_node = node
        className = node.__class__.__name__
        meth = getattr(self, 'visit' + className, self.visit)
        meth(node)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#        Visitors 
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

class NameReplacer(PostorderVisitor):
    """Replace names in a tree with alternate names"""
    
    def __init__(self):
        compiler.visitor.ASTVisitor.__init__(self)
        
    def replace_names(self,tree,replacements):
        self.replacements = replacements
        postorder(s, tree)

    def visitName(self, node):
        if self.replacements.has_key(node.name):
            node.name = self.replacements[node.name]

class NameConstReplacer(PostorderVisitor):
    """Replace names in a tree with constant values."""
    
    def __init__(self):
        PostorderVisitor.__init__(self)
        
    def replace_namevals(self,tree,replacements):
        self.replacements = replacements
        self.postorder(tree)

    def visitName(self, node):
        if self.replacements.has_key(node.name):
            newnode = ast.Const(self.replacements[node.name])
            newnode.lineno = node.lineno
            self.replace(newnode)

def getFunctionTree(function):
    return GetFunctionTree().tree(function)

class GetFunctionTree(compiler.visitor.ASTVisitor):
    """Visitor that finds the first function definition in an AST"""
    def __init__(self):
        compiler.visitor.ASTVisitor.__init__(self)

    def tree(self,func):
        """Returns the AST tree for a for a function. Raises an
        IOError if the tree can not be found"""
        self.func = func
        self.func_tree = None
        try:
            src = inspect.getsource(self.func)
            # remove leading whitespace from the source (this way, if the
            # function is indented (as in a nested function definition)
            # we can still compile it
            i = 0
            while i<len(src):
                if not src[i] in string.whitespace:
                    break
                i+=1
            src = src[i:]
        except IOError:
            raise "Could not get source code for %s, func must be in a file" %\
                  self.func.__name__
        tree = compiler.parse(src,"exec")
        set_filename("__none__", tree)
        self.preorder(tree,self)
        return self.func_tree
        
    def visitFunction(self, node):
        if node.name==self.func.__name__:
            self.func_tree = node

class FuncVisitor(compiler.visitor.ASTVisitor):
    def __init__(self):
        compiler.visitor.ASTVisitor.__init__(self)
        self.funcs = {}

    def visitFunction(self, node):
        args, hasTupleArg = pycodegen.generateArgList(node.argnames)
        lnf = compiler.walk(node.code, NameFinder(args), verbose=0)
        self.funcs[node.name] = lnf

class NameFinder(pycodegen.LocalNameFinder):
    """Finds local and global names in a function"""
    def __init__(self, names=()):
        pycodegen.LocalNameFinder.__init__(self,names)
        self.read_names = misc.Set()        

    def visitName(self, node):
        self.read_names.add(node.name)
    
    def getLocals(s):
        names = s.names.copy()
        for elt in s.globals.elements():
            if names.has_elt(elt):
                names.remove(elt)
        return names
    
    def getGlobals(s):
        locals = s.getLocals()
        names = s.names.copy()
        for name in s.read_names.elements(): names.add(name)
        for elt in locals.elements():
            if names.has_elt(elt):
                names.remove(elt)
        return names


# Should probably add error checking to this too.
class EliminateCSE(PostorderVisitor):
    """Eliminates constant sub-expressions"""
    def eliminate(self,tree):
        self.postorder(tree)
    

    def visitAdd(self, node): self.try_binary(node,lambda x,y: x+y)
    def visitSub(self, node): self.try_binary(node,lambda x,y: x-y)    
    def visitDiv(self, node): self.try_binary(node,lambda x,y: x/y)
    def visitMul(self, node): self.try_binary(node,lambda x,y: x*y)

    def visitUnaryAdd(self, node): self.try_unary(node,lambda x: +x)
    def visitUnarySub(self, node): self.try_unary(node,lambda x: -x)

    def try_binary(self,node,func):
        if isinstance(node.left,ast.Const) and isinstance(node.right,ast.Const):
            self.replace(ast.Const(func(node.left.value,node.right.value)))
    
    def try_unary(self,node,func):
        if isinstance(node.expr,ast.Const):
            self.replace(ast.Const(func(node.expr.value)))

    def visitSliceobj(self,node):

        if reduce(lambda x,y: x and isinstance(y,ast.Const),node.nodes,1):
            sl = apply(slice,map(lambda x: x.value,node.nodes))
            self.replace(ast.Const(sl))

# XXX Check for and raise an error on recursive inlining. 
class FuncInliner(PostorderVisitor):
    def __init__(self):
        compiler.visitor.ASTVisitor.__init__(self)
        self.funcs = {}

    def inline(self,tree,namespace):
        self.inlineno = 0 # number of current inlined name (for mangling locals)
        self.namespace = namespace

    def get_inlined_func_tree(self,node):
        """Returns the AST tree for a function rooted at node."""
        lineno = node.node_info.lineno
        if not isinstance(node.node,ast.Name):
            raise SyntaxError, \
               "line %s: can't use expressions for inlined functions" % lineno
        inline_func = get_value(node.node.name,self.namespace)
        tree = getFunctionTree(func)
        
        
    def CallFunc(self,node):
        if isinstance(node.node,ast.Name) and node.node.name=="inline":
            lineno =  node.node_info.lineno
            if len(node.args)!=1:
                raise SyntaxError, \
                    "line %s: inline(func) only accepts one argument" % lineno
            to_inline = node.args[0]
            if not isinstance(to_inline,ast.CallFunc):
                raise SyntaxError, \
                     "line %s: must inline a function call number" % lineno
#            if not len(to_inline.args)==0:
#                raise SyntaxError,
#                   "line %s: inlined functions can not have arguments" % lineno
            

class CheckRules(PostorderVisitor):
    """Checks the rules for a STEP rule"""
    def check(self,tree,func):
        self.func = func
        self.startlineno =  self.func.func_code.co_firstlineno - 1
        self.postorder(tree)

    def syntax_str(self,node,str):
        head = "line %i: "  % (node.lineno + self.startlineno)
        return head+str
    
    def visitGlobal(self, node):
        raise SyntaxError, self.syntax_str(node, \
               "can't use global definitions in rule functions")
    def visitContinue(self, node):
        raise SyntaxError, self.syntax_str(node, \
               "can't use continue statements in rule functions")
    def visitLambda(self, node):
        raise SyntaxError, self.syntax_str(node, \
               "can't use lambda statements in rule functions")
    def visitYield(self, node):
        raise SyntaxError, self.syntax_str(node, \
               "can't use yield statements in rule functions")
    def visitRaise(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't raise execptions in rule functions")
    def visitExec(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use exec statements in rule functions")
    def visitAssert(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use assert statements in rule functions")

    def visitTry(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use try statements execptions in rule functions")
    def visitTryFinally(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use finally statements in rule functions")
    def visitTryExcept(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use except statements in rule functions")
    def visitListComp(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use list comprehension statements in rule functions")
    def visitListCompFor(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use list comprehension statements in rule functions")
    def visitListCompIf(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use list comprehension statements in rule functions")
    def visitReturn(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use return statements in rule functions")
    def visitFunction(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't declare new functions in a rule")
    def visitBreak(self,node):
        raise SyntaxError, self.syntax_str(node, \
            "can't use break statements in rule functions")


import step

class ReplaceSignalsBase:

    def doit(self,tree,namespace,exclude):
        """Replace signals in tree with names from 'namespace' excluding
        signals in the exclude dictionary (ie. function locals).
        """
        self.exclude = exclude # names to exclude                
        self.namespace = namespace
        self.proxy_names = {}  # output signals to their proxy names
        self.postorder(tree)
        return self.proxy_names # pn[`signal`] = [proxyname,signal]

    def new_proxyname(self):
        newname = self.proxy_basename+`len(self.proxy_names)`
        return newname

    def get_proxyname(self,node):
        """If the node references a signal or a subscripted signal, it
        returns the proxy name to be used for it. Adds the signal to the
        list of outputs. Returns None if the expression is not a signal name."""
        # Get the name directly or the subscripted name and neighbor
        # subscript
        if isinstance(node,ast.Subscript):
            if isinstance(node.expr,ast.Name):
                name = node.expr.name
                subs = node.subs
            else: return None
        elif isinstance(node,ast.Name):
            name = node.name
            subs = None
        else: return None

        found = 0
        if name in self.exclude: return None
        for ns in self.namespace:
            if ns.has_key(name):
                sig = ns[name]; found=1; break
        if not found: return None

        # Subscript the signal to get the object (may raise an error if the
        # object is already a slice. 
        if subs!=None:
            # try to get the (constant) values for the subscripts
            if not reduce(lambda x,y: x and isinstance(y,ast.Const),subs,1):
                # XXX add line number reporting
                raise SyntaxError, \
                 "Unable to reduce the subscript for %s to a constant" % name
            subs =  map(lambda x: x.value,subs)
            if not isinstance(sig,step.SignalRegion):
               sig = sig.__getitem__(subs)
            else:
               raise IndexError, \
                "Tried to subscript %s, can not subscript a SignalRegion" % name
        else:
            # get the SignalRegion at an offset of zero if this is a signal
            if not isinstance(sig,step.SignalRegion):
                sig = sig.__getitem__([0]*sig.nd)

        # Use the string representation of the signal (identification and
        # the neighbor offsets) to get the correct proxy name.  This
        # allows a SignalRegion to normalize subscripts, etc. 
        if self.proxy_names.has_key(repr(sig)):
            proxyname = self.proxy_names[repr(sig)][0]
        else:
            proxyname = self.new_proxyname()
            self.proxy_names[repr(sig)] = [proxyname,sig]
        return proxyname

class ReplaceInputSignals(ReplaceSignalsBase,PostorderVisitor):
    """Replaces output signals and signal slices with proxy names"""
    proxy_basename = "input_proxy_"
    def __init__(self):
        PostorderVisitor.__init__(self)

    def doit(self,tree,namespace,exclude):
        self.exclude = exclude # names to exclude
        self.namespace = namespace
        self.proxy_names = {}  # output signals to their proxy names
        self.phase = 0;  self.postorder(tree)
        self.phase = 1;  self.postorder(tree)
        return self.proxy_names

    def visitName(self,node):
        if self.phase==0: return
        newname = self.get_proxyname(node)
        if newname!=None:
          hash(newname)
          name_node = ast.Name(newname)
          name_node.lineno = node.lineno
          self.replace(name_node)

    def visitSubscript(self,node):
        if self.phase==1: return
        newname = self.get_proxyname(node)
        if newname!=None:
          hash(newname)
          name_node = ast.Name(newname)
          name_node.lineno = node.lineno
          self.replace(name_node)        


class ReplaceOutSignals(ReplaceSignalsBase,PostorderVisitor):
    """Replaces output signals and signal slices with proxy names"""
    proxy_basename = "output_proxy_"
    def __init__(self):
        PostorderVisitor.__init__(self)

    def visitAssign(self,node):
        for i in xrange(len(node.nodes)):
          ass_node = node.nodes[i]
          if isinstance(ass_node,ast.AssAttr) and ass_node.attrname=="_":
              # if assigning to the output attribute
              obj_expr = ass_node.expr
              newname = self.get_proxyname(obj_expr)
              if newname==None: return
              # replace the sub-tree with a set of names
              hash(newname)
              name_node = ast.AssName(newname,'OP_ASSIGN')
              name_node.lineno = obj_expr.lineno
              node.nodes[i] = name_node

    def visitAssTuple(self,node):
        self.visitAssign(node)
        

class FindAlwaysAssignedSignals(PostorderVisitor):
    """Find output signals whose value are always assigned by analyzing
    the AST control flow structure. Deposit the results, a dictionary of the
    names that are always assigned, in the __outnames__ attribute of 
    the top level Stmt node.
    """
    proxy_basename = "output_proxy_"
    def __init__(self):
        PostorderVisitor.__init__(self)

    def doit(self,tree):
        self.topoutnamedict = {}        
        self.postorder(tree)
        return self.topoutnamedict

    def add_ancestor_stmt_outname(self,name):
        i = len(self.node_stack)-1
        while i>=0:
            ancestor = self.node_stack[i][self.indx_stack[i]]
            if isinstance(ancestor,ast.Stmt):
                if not hasattr(ancestor,"__outnames__"):
                    ancestor.__outnames__ = {name:0}
                else:
                    ancestor.__outnames__[name] = 0
                self.topoutnamedict = ancestor.__outnames__
                return
            i-=1
        raise Exception, """There is no containing statement for %s.
        Please report this bug.""" % name
        
    def visitAssName(self,node):
        # if the name is in the dictionary of outpouts, propagate the
        # dictionary up to the statement containing the assignment.
        try:
            base = node.name[0:len(self.proxy_basename)]
        except:
            return
        if base==self.proxy_basename:
            self.add_ancestor_stmt_outname(node.name)

    def visitIf(self,node):
        if node.else_==None or not hasattr(node.else_,"__outnames__"):
            self.topoutnamedict = {}
            return # can't cover all cases if the outputs are not set here.
        outname_dicts = [node.else_.__outnames__]
        for cond,stmt in node.tests:
            if not hasattr(stmt,"__outnames__"):
                self.topoutnamedict = {}
                return
            outname_dicts.append(stmt.__outnames__)
        outnames = reduce(set_intersection,outname_dicts)
        if len(outnames)==0:
            self.topoutnamedict = {}
            return
        for name in outnames.keys():
            self.add_ancestor_stmt_outname(name)
        
# class DecorateTypes(PostorderVisitor):

class EnsureDereferenced(PostorderVisitor):
    """Ensure that all of the names have been dereferenced"""
    def doit(self,tree,signal_names):
        self.signal_names = signal_names
        self.postorder(tree)
        
    def visitName(self,node):
        if self.signal_names.has_key(node.name):
            raise step.StepError, "line %s: Invalid use of a signal" % \
                 node.lineno
          
#     def visitAugAssign(self,node):
#         print node
#         raise Exception, "Don't know how to parse this"

class RuleStrober:
    """Strobe a rule function"""
    signal_types = (step.Signal,step.OutSignal,step.SignalRegion)# ,step.Bundle
    def __init__(self,func,namespace={}):
        self.func = func; self.namespace = namespace
        tree = getFunctionTree(func)
        func_body = tree.code
        # make sure that the proper rule syntax is followed 
        CheckRules().check(func_body,func)   
        nf = compiler.walk(func_body,NameFinder())
        global_names = nf.getGlobals()
        local_names = nf.getLocals()        
        replacements = {}
        signals = {}
        for name in global_names.elements():
           found = 0
           for ns in namespace:
               if ns.has_key(name):
                   val = ns[name]; found = 1
                   is_sig = reduce(lambda x,type: x or isinstance(val,type),
                                   self.signal_types,0)
                   if not is_sig:
                       replacements[name] = val
                   else:
                       signals[name] = val
                   # XXX should probably check for mutable types here too!
                   break
           if not found:
               raise NameError, "'%s' is not defined" % name
        NameConstReplacer().replace_namevals(tree,replacements)
        EliminateCSE().eliminate(tree)

        self.output_proxies = ReplaceOutSignals().doit(tree,
                                              namespace,local_names)

        
        self.input_proxies = ReplaceInputSignals().doit(tree,
                                                        namespace,local_names)

        # Raise an error if a signal has not been dereferenced. 
        EnsureDereferenced().doit(tree,signals)
        self.tree = tree
        self.set_output_defaults()
        self.make_module()
        
    def set_output_defaults(self):
        """Modify the AST and the parameters so that the correct default
        values for output signals are always written.

        The default value for an OutSignal output value is 0. 

        The default value for a Signal output value is the current value.
        If the signal is not always assigned, add the current value to the
        inputs and generate an input proxy argument. 
        """
        # The nodes look like the following 
        #  zero assignment:
        #   Assign([AssName('__out_proxy__', 'OP_ASSIGN')], Const(0))
        #  input assignment:
        #   Assign([AssName('__out_proxy__', 'OP_ASSIGN')], Name('__in_proxy__')
        
        self.output_keys = self.__ordered_keys__(self.output_proxies)
        self.output_proxy_names = map(lambda x: self.output_proxies[x][0],
                                      self.output_keys)

        # Get proxy names for the signals that need defaults
        always_assigned = FindAlwaysAssignedSignals().doit(self.tree)
#        print "always assigned", always_assigned

        need_defaults = set_disjoint(make_set(self.output_proxy_names),
                                     make_set(always_assigned))
#        print "need_defaults",need_defaults

        # Use the proxy names to lookup the associated signals
        proxyname_to_sig = {}
        for name,sig in self.output_proxies.values():
            proxyname_to_sig[name] = sig

#        print need_defaults
        
        need_defaults = \
                maplisttodict(need_defaults.keys(),proxyname_to_sig)

        # For regular Signal objects, lookup the corresponding
        # input signal proxy name and create an assignment. Generating a new
        # input and proxy name if necessary.  For OutSignal objects,
        # set the default value to zero.
        assignments = []
        for proxyname,sigregion in need_defaults.items():
            lhs_value = ast.AssName(proxyname,'OP_ASSIGN')
            if isinstance(sigregion.base_signal(),step.OutSignal):
                rhs_value = ast.Const(0)
            else:
                # get the corresponding input
                if not self.input_proxies.has_key(`sigregion`): # add to inputs
                    inproxyname = "input_proxy_"+`len(self.input_proxies)`
                    self.input_proxies[`sigregion`] = [inproxyname,sigregion]
                else:
                    inproxyname = self.input_proxies[`sigregion`][0]
                rhs_value = ast.Name(inproxyname)
            assignments.append(ast.Assign([lhs_value],rhs_value))

        # add the default val assignment nodes to the beginning of the function 
        self.tree.code.nodes = assignments+self.tree.code.nodes

        # now that the inputs have been finalized, we can create some
        # useful secondary data structures. 
        self.input_keys = self.__ordered_keys__(self.input_proxies)
        self.input_proxy_names = map(lambda x: self.input_proxies[x][0],
                                     self.input_keys)


    def make_module(self):
        """Modify the AST so that it can be sourced to create a python
        module defining the transition function, then get the transition
        function and bind it to __strobed_func__ so that the strobed
        function may be called. 
        """
        
        # INPUT ARGUMEMENTS (signals)
        self.tree.argnames = self.input_proxy_names

        # OUTPUT RETURN VALUES
        ret = ast.Return(ast.List(map(ast.Name,self.output_proxy_names)))
        self.tree.code.nodes = self.tree.code.nodes+[ret]
        
        # CREATE THE MODULE
        tree =ast.Module("",ast.Stmt([self.tree]))
        misc.set_filename("__none__",tree)
        gen = pycodegen.ModuleCodeGenerator(tree)
        code = gen.getCode()
        mod = {} # namespace
        eval(code,mod)
        self.mod = mod
        self.__strobed_func__ = mod[self.func.func_name]
        
    def __ordered_keys__(self,dict):
        # return the (signal) keys of the dictionary in a lexicographical 
        # order of the proxy names
        def sort_func(a,b):
            if a[0]<b[0]: return -1
            if a[0]>b[0]: return 1
            return 0

        values = dict.values();
        values.sort(sort_func)
        return map(lambda x: repr(x[1]),values)  

    def inputs(self):
        return map(lambda x: self.input_proxies[x][1],self.input_keys)

    def outputs(self):
        return map(lambda x: self.output_proxies[x][1],self.output_keys)

    def iotypedict(self):
        typedict = {}
        inputs = self.inputs();
        for i in xrange(len(inputs)):
            typedict[self.input_proxy_names[i]] = \
                 step.numarraytypetostr(inputs[i].base_signal().type)

        outputs = self.outputs();
        for i in xrange(len(outputs)):
            typedict[self.output_proxy_names[i]] = \
                 step.numarraytypetostr(outputs[i].base_signal().type)
        return typedict

    def __call__(self,inputs,outputs=None):
        return apply(self.__strobed_func__,inputs)        
#        if outputs==None:
#        else:
#            return apply(self.__strobed_func__,inputs+outputs)

    def hash_string(self):
        """Returns an identifying hash string"""
        hash = "\ninputs:"
        for sig in self.inputs(): hash+=`sig.base_signal().type`
        hash+="\noutputs:"
        for sig in self.outputs(): hash+=`sig.base_signal().type`
        hash+="\ncode:"+`self.tree`
        return hash
   
        
                         
#    def __call__(self,inputs,default_outputs):
#        for i in xrange(len(inputs)):
#            self.mod[self.input_proxy_names[i]]=inputs[i]
#            # XXX should set default output values too
#        for i in xrange(len(default_outputs)):
#            self.mod[self.output_proxy_names[i]]=default_outputs[i]
#        self.call()
#        return map(lambda x: self.mod[x],self.output_proxy_names)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                          SPECIAL FUNCTIONS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def set_filename(filename, tree):
    """Set the filename attribute to filename on every node in tree"""
    worklist = [tree]
    while worklist:
        node = worklist.pop(0)
        node.filename = filename
        worklist.extend(node.getChildNodes())

class NodeInfo: pass
   # lineno
   # filename

def update_info(tree,func):
    """Update the nodes of every tree with special information used here."""
    lineoffset = func.func_code.co_firstlineno-1
    filename = func.func_code.co_filename
    worklist = [tree]
    while worklist:
        node_info = NodeInfo()
        node = worklist.pop(0)
        try:
          node_info = node.lineno+lineoffset
        except: node.lineno = -1
        node.node_info = lineno
        node.filename = filename
        worklist.extend(node.getChildNodes())

def get_value(name,namespaces):
    for ns in namespaces:
        if ns.has_key(name):
            return ns[name]
    raise NameError, "%s is not defined"


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                          C code generator
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Generate C  from an AST.
import types
class CCodeGenen(PostorderVisitor):
    error_str = "C code generator can't handle %s"
    def getc(self,tree):
        """Get the C code"""
        self.postorder(tree)
        return tree.__ccode__

    def visitSlice(self,node): raise Exception, self.error_str % "slices"
    def visitConst(self,node):
        tp = type(node.value)
        if not (tp==types.IntType or tp==types.FloatType):
            parent = self.parent()
            if not isinstance(parent,Discard):
              raise Exception, \
        "Invalid type for a constant %s (only float and int are allowed" % tp

        node.__ccode__ = `node.value`
    def visitRaise(self,node):raise Exception, self.error_str % "exceptions"
    def visitAssTuple(self,node):raise Exception, self.error_str % \
        "list assignment"
    def visitMul(self,node):
        node.__ccode__ = "(%s*%s)" % (node.left.__ccode__,node.right.__ccode__)
    def visitDiv(self,node):
        node.__ccode__ = "(%s/%s)" % (node.left.__ccode__,node.right.__ccode__)
    def visitInvert(self,node):
        node.__ccode__ = "(~%s)" % (node.expr.__ccode__)
    def visitRightShift(self,node):
        node.__ccode__ = "(%s>>%s)" % (node.left.__ccode__,node.right.__ccode__)
    def visitAssList(self,node):
        raise Exception, self.error_str % "list assignment"
    def visitFrom(self,node):
        raise Exception, self.error_str % "import statements"
    def visitGetattr(self,node):
        raise Exception, self.error_str % "object attributes"
    def visitDict(self,node):
        raise Exception, self.error_str % "dictionary constructors"
    def visitModule(self,node):
        raise Exception, self.error_str % "module declarations"
    def visitExpression(self,node):
        raise Exception, self.error_str % "eval statements"
    def visitExpression(self,node):
        raise Exception, self.error_str % "eval statements"
    def UnaryAdd(self,node): # do nothing
        node.__ccode__ = node.expr.__ccode__
    def visitEllipsis(self,node):
        raise Exception, self.error_str % "ellipses"
    def visitPrint(self,node): 
        raise Exception, self.error_str % "print statements"        
    def visitImport(self,node): 
        raise Exception, self.error_str % "import statements"
    def visitSubscript(self,node):
        raise Exception, self.error_str % "subscripts"
    def visitTryExcept(self,node):
        raise Exception, self.error_str % "Try statements"
    def visitOr(self,node):
        code = node.nodes[0].__ccode__
        for nd in node.nodes[1:]:
            code+="||"+nd.__ccode__
        node.__ccode__ = "("+code+")"
    def visitName(self,node):
        node.__ccode__ = node.name
    def visitFunction(self,node):
        # XXX must figure out how to handle this
        node.__ccode__ = node.code.__ccode__
    def visitAssert(self,node):
        raise Exception, self.error_str % "assert statements"
    def visitReturn(self,node):
        node.__ccode__ = "" # XXX must figure out how to handle this        
    def visitPower(self,node):
        # XXX maybe shouldn't do this...
        raise Exception, self.error_str % "the ** operator"        
        node.__ccode__ = "pow(%s,%s)" % \
            (node.left.__ccode__,node.right.__ccode__)
    def visitExec(self,node):
        raise Exception, self.error_str % "exec statements"        
    def visitStmt(self,node):
        node.__ccode__ = \
           reduce(lambda x,y: x+y.__ccode__,node.getChildren(),"")
    def visitSliceobj(self,node):
        raise Exception, self.error_str % "slice statements"        
    def visitBreak(self,node):
        raise Exception, self.error_str % "break statements"
    def visitBitand(self,node):
        code = node.nodes[0].__ccode__
        for nd in node.nodes[1:]:
            code+="&"+nd.__ccode__
        node.__ccode__ = "("+code+")"
    def visitFloorDiv(self,node):
        raise Exception, self.error_str % "floor division"
    def visitTryFinally(self,node):
        raise Exception, self.error_str % "try finally statements"
    def visitNot(self,node):
        node.__ccode__ = "(!%s)" %  (node.expr.__ccode__)
    def visitClass(self,node):
        raise Exception, self.error_str % "class declarations"
    def visitMod(self,node):
        node.__ccode__ = "(%s%%s)" %  (node.left.__ccode__,node.right.__ccode__)

    
    def visitPrintnl(self,node):
        raise Exception, self.error_str % "print statements"
    def visitTuple(self,node):
        raise Exception, self.error_str % "tuple declarations"
    def visitAssAttr(self,node):
        raise Exception, self.error_str % "attribute assignments"
    def visitKeyword(self,node):
        raise Exception, self.error_str % "function calls (keyword args)"

    def visitAugAssign(self,node):
        raise Exception, self.error_str % "AugAssign statements? (please email example to tbach@bu.edu)"
    def visitList(self,node):
        raise Exception, self.error_str % "list declarations"
    def visitYield(self,node):
        raise Exception, self.error_str % "yield generator statements"
    def visitLeftShift(self,node):
        node.__ccode__ = "(%s<<%s)" % (node.left.__ccode__,node.right.__ccode__)
    def visitAssName(self,node):
        #XXX should maybe handle other flags
        if node.flags!="OP_ASSIGN":
            raise Exception, \
              "don't know how to handle the AssName with %s flags" % node.flags
        node.__ccode__ = "%s" % node.name
    def visitWhile(self,node):
        if node.else_ != None:
            raise Exception, \
              "don't know how to handle while statements with else statements"
        bodycode = node.body.__ccode__.replace("\n","\n    ") # indent
        code = "\nwhile (%s){%s\n}" % (node.test.__ccode__,)
        node.__ccode__ = code
    def visitContinue(self,node):
        raise Exception, self.error_str % "continue statements"
    def visitBackquote(self,node):
        raise Exception, self.error_str % "backquote statements"    
    def visitDiscard(self,node):
        # XXX we throw away the code, but this may be bad since the necessary
        # side effects aren't taken care of.
        node.__ccode__ = ""
    def visitAssign(self,node):
        if len(node.nodes)>1:
            raise Exception, self.error_str % "list comprehension assignments"
        ass = node.nodes[0]
        node.__ccode__ = "\n%s = %s;" % (ass.__ccode__,node.expr.__ccode__)
    def visitLambda(self,node):
        raise Exception, self.error_str % "lambda statements"
    def visitAnd(self,node):
        code = node.nodes[0].__ccode__
        for nd in node.nodes[1:]:
            code+="&&"+nd.__ccode__
        node.__ccode__ = "("+code+")"
#        code = reduce(lambda x,y: x.__ccode__+"&&"+y.__ccode__,node.nodes)
#        node.__ccode__ = "(%s)" % (code)
    def visitCompare(self,node):
        if len(node.ops)!=1:
            raise Exception, self.error_str % "list comparisons"
        op,rhs = node.ops[0]
        node.__ccode__ = "(%s%s%s)" % (node.expr.__ccode__,op,rhs.__ccode__)
    def visitBitor(self,node):
        code = node.nodes[0].__ccode__
        for nd in node.nodes[1:]:
            code+="|"+nd.__ccode__
        node.__ccode__ = "("+code+")"
    def visitBitxor(self,node):
        code = node.nodes[0].__ccode__
        for nd in node.nodes[1:]:
            code+="^"+nd.__ccode__
        node.__ccode__ = "("+code+")"        
    def visitCallFunc(self,node):
        str = self.error_str % "generic function calls\n"+ \
              "only float() and int() are allowed"
        if not (isinstance(node.node,ast.Name) and \
                (node.node.name=="float" or (node.node.name=="int"))):
             raise Exception, str
        if not (len(node.args)==1 and \
                self.star_args==None and self.dstar_args):
             raise Exception, "float() or int() takes exactly one argument"
        arg = node.args[0]
        node.__ccode__ = "((%s) %s)" % (node.node.name,arg.__ccode__)
        
    def visitGlobal(self,node):
        raise Exception, self.error_str % "global statements"    
    def visitAdd(self,node):
        node.__ccode__ = "(%s+%s)" %  (node.left.__ccode__,node.right.__ccode__)
    def visitListCompIf(self,node):
        raise Exception, self.error_str % "list comprehension statements"
    def visitSub(self,node):
        node.__ccode__ = "(%s-%s)" %  (node.left.__ccode__,node.right.__ccode__)
    def visitPass(self,node):
        raise Exception, self.error_str % "pass statements"    
    def visitUnarySub(self,node):
        node.__ccode__ = "(%s-%s)" %  (node.left.__ccode__,node.right.__ccode__)
    def visitIf(self,node):
        cond,stmt=node.tests[0]
        stmtcode = stmt.__ccode__.replace("\n","\n    ") # indent
        code = """\nif (%s){%s\n}""" % (cond.__ccode__,stmtcode)
        for cond,stmt in node.tests[1:]:
            stmtcode = stmt.__ccode__.replace("\n","\n    ") # indent
            code+=" else if (%s) {%s\n}" % (cond.__ccode__,stmtcode)
        if node.else_ != None:
            stmtcode = node.else_.__ccode__.replace("\n","\n    ") # indent
            code+=" else {%s\n}" % stmtcode
        node.__ccode__ = code
    def visitListComp(self,node):
        raise Exception, self.error_str % "list comprehension statements"    
    def visitListCompFor(self,node):
        raise Exception, self.error_str % "list comprehension for statements"



# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                          TYPE ANALYSIS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
precedence = {None: 0,
              "UInt8":1,"Int8":1,
              "UInt16":3,"Int16":3,
              "UInt32":5,"Int32":5,
              "Float32":7}

def mathopcoerce(a,b):
    if precedence[a]>precedence[b]: return a
    return b

def bitopcoerce(a,b):
    if a == "Float32" or b=="Float32":
        raise Exception, "Can not use Float32 types in bit operations"
    return mathopcoerce(a,b)

BOOLEAN_TYPE = "Int32"

class CCodeTypeInference(PostorderVisitor):
    def get_types(self,tree,iotypes={},vartypes={}):
        """ tree: tree for the code
        types : dictionary mapping names to types. none if doesn't have a type
        """
        self.iotypes = iotypes
        self.vartypes = vartypes
        self.postorder(tree)
        return self.vartypes
        
    def visitConst(self,node):
        tp = type(node.value)
        if (tp==types.IntType): node.__type__ = "Int32"
        elif (tp==types.FloatType): node.__type__ = "Float32"
    def visitMul(self,node):
        try: node.__type__=mathopcoerce(node.left.__type__,node.right.__type__)
        except AttributeError: pass

    def visitInvert(self,node):
        try: node.__type__ = node.expr.__type__
        except AttributeError: pass
    def visitRightShift(self,node):
        try: bitopcoerce(node.left.__type__,node.left.__type__)
        except AttributeError: pass
        node.__type__ = node.left.__type__
    def UnaryAdd(self,node): # do nothing
        try: node.__type__ = node.expr.__type__
        except AttributeError: pass
    def visitOr(self,node):
        node.__type__ = BOOLEAN_TYPE
    def visitName(self,node):
        type = mathopcoerce(self.iotypes.get(node.name),
                     self.vartypes.get(node.name))
        if type==None: return
        node.__type__ = type
    def visitBitand(self,node):
        try: node.__type__ = \
             reduce(lambda x,y: bitopcoerce(x.__type__,y.__type__),node.nodes)
        except AttributeError: pass
    def visitNot(self,node):
        node.__type__ = "UInt8"
    def visitMod(self,node):self.visitMul(node)
    def visitLeftShift(self,node):
        try: bitopcoerce(node.left.__type__,node.left.__type__)
        except AttributeError: pass
        node.__type__ = node.left.__type__
#    def visitAssName(self,node):
        #XXX should maybe handle other flags
#        try: bitopcoerce(node.left.__type__,node.left.__type__)
#        except AttributeError: pass
        
    def visitAssign(self,node):
        try: type = node.expr.__type__
        except AttributeError: return
        ass = node.nodes[0]
        if not isinstance(ass,ast.AssName):
            raise Exception, "Don't know how to handle Assign(%s)" % node
        name = ass.name
        # XXX need to handle the case of multiple types here...
        # XXX probably shouldn't change the type of output signal objects
        # (float and int are incompatible) 
        self.vartypes[name] = type
    def visitAnd(self,node):
        node.__type__ = BOOLEAN_TYPE
    def visitBitor(self,node):
        self.visitBitand(node)
    def visitBitxor(self,node):
        self.visitBitand(node)        
    def visitCallFunc(self,node):
        if not isinstance(node.node,ast.Name):
            return
        name = node.node.name
        if name=="float":  node.__type__ = "Float32"
        elif name=="int":  node.__type__ = "Int32"
    def visitAdd(self,node): self.visitMul(node)
    def visitSub(self,node): self.visitMul(node)
    def visitDiv(self,node): self.visitMul(node)        
    def visitUnarySub(self,node): self.visitUnaryAdd(node)
    def visitCompare(self,node):
        node.__type__ = BOOLEAN_TYPE



def getvartypes(tree,iotypes):
    ccti = CCodeTypeInference()
    vartypes={}; updatedvartypes={}; init = 1
    while ((vartypes!=updatedvartypes) or init):
        init = 0
        vartypes = updatedvartypes
        updatedvartypes = ccti.get_types(tree,iotypes,copy.copy(vartypes))
    return updatedvartypes

        
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#                          TESTING
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import unittest
class TestAST(unittest.TestCase):

   def testSimpleCSE(self):
       src = "1/2.+4*2"
       tree = compiler.parse(src,"exec")
       EliminateCSE().postorder(tree)
       tree_expect = Module(None, Stmt([Discard(Const(1/2.+4*2))]))
       self.assert_(tree_expect.asList()==tree.asList())
       

   def testNestedCSE1(self):
       src = "[1/2.+4*2]"
       tree = compiler.parse(src,"exec")
       EliminateCSE().postorder(tree)
       tree_expect = Module(None, Stmt([Discard(List([Const(8.5)]))]))
       self.assert_(tree_expect.asList()==tree.asList())
       

   def testNestedCSE2(self):
       src = "b[1] = a[1/2.+4*2]"
       tree = compiler.parse(src,"exec")
       EliminateCSE().postorder(tree)
       tree_expect = Module(None, Stmt([Assign([Subscript(Name('b'),
                       'OP_ASSIGN', [Const(1)])], Subscript(Name('a'),
                       'OP_APPLY', [Const(8.5)]))]))
       self.assert_(tree_expect.asList()==tree.asList())
       
   def testNestedCSE3(self):
       src = "b[1+2:1,-1]._ = a[1/2.+4*2]"
       tree = compiler.parse(src,"exec")
       EliminateCSE().postorder(tree)
       tree_expect = Module(None, Stmt([Assign([AssAttr(Subscript(Name('b'),
                       'OP_APPLY', [Const(slice(3, 1)), Const(-1)]),
                        '_', 'OP_ASSIGN')], Subscript(Name('a'), 'OP_APPLY',
                        [Const(8.5)]))]))
       self.assert_(tree_expect.asList()==tree.asList())


def test():
    suite = unittest.makeSuite(TestAST,'test')
    unittest.TextTestRunner(verbosity=0).run(suite)

if __name__=="__main__":
    test()


def test_inline(a=1,b=2):
    a = 1
    print "Inline",a,b

def test_rule():
    a = 2
    inline(test_inline(3))
    print "test",a


# print getFunctionTree(test_inline)
# --------------------------------


