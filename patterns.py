""" 
Pattern classes go here
"""

import math
from core import *

TEXT_CHARS = ( "".join([chr(x) for x in range(ord('0'),ord('9')+1)])
				+ "".join([chr(x) for x in range(ord('A'),ord('Z')+1)])
				+ "".join([chr(x) for x in range(ord('a'),ord('z')+1)]) )


class LiteralPattern(Pattern):

	pos = None
	char = None
	
	def matcher(self):
		self.curr = yield
		self.pos = self.curr.col,self.curr.row
		self.char = self.curr.char
		if( not self.occupied() and not self.curr.char.isspace()
				and not self.curr.char in (START_OF_INPUT,END_OF_INPUT) ):
			yield M_OCCUPIED
		else:
			self.reject()
		return
		
	def render(self):
		Pattern.render(self)
		return [ Text(pos=self.pos,z=0,text=self.char,colour=C_FOREGROUND,alpha=1.0,size=1) ]
		
		
class DbCylinderPattern(Pattern):

	tl = None
	br = None
	
	def matcher(self):
		w,h = 0,0
		self.curr = yield
		self.tl = (self.curr.col,self.curr.row)
		self.curr = yield self.expect(".",M_OCCUPIED|M_BOX_START_S|M_BOX_START_E)
		self.curr = yield self.expect("-",M_OCCUPIED|M_BOX_START_S)
		while self.curr.char != ".":
			self.curr = yield self.expect("-",M_OCCUPIED|M_BOX_START_S)
		w = self.curr.col-self.tl[0]+1
		self.curr = yield self.expect(".",M_OCCUPIED|M_BOX_START_S)
		self.curr = yield M_BOX_AFTER_E
		for meta in self.await_pos(self.offset(0,1,self.tl)):
			self.curr = yield meta
		self.curr = yield self.expect("'",M_OCCUPIED|M_BOX_START_E)
		for n in range(w-2):
			self.curr = yield self.expect("-",M_OCCUPIED)
		self.curr = yield self.expect("'",M_OCCUPIED)
		self.curr = yield M_BOX_AFTER_E
		for meta in self.await_pos(self.offset(0,2,self.tl)):
			self.curr = yield meta
		while True:	
			linestart = self.curr.col,self.curr.row
			self.curr = yield self.expect("|",M_OCCUPIED|M_BOX_START_E)
			for meta in self.await_pos(self.offset(w-2,0)):
				self.curr = yield meta
			self.curr = yield self.expect("|",M_OCCUPIED)
			self.curr = yield M_BOX_AFTER_E
			for meta in self.await_pos(self.offset(0,1,linestart)):
				self.curr = yield meta
			if self.curr.char == "'": break
		linestart = self.curr.col,self.curr.row
		self.curr = yield self.expect("'",M_OCCUPIED|M_BOX_START_E)
		for n in range(w-2):
			self.curr = yield self.expect("-",M_OCCUPIED)
		self.br = (self.curr.col,self.curr.row)
		self.curr = yield self.expect("'",M_OCCUPIED)
		try:
			self.curr = yield M_BOX_AFTER_E
			for meta in self.await_pos(self.offset(0,1,linestart)):
				self.curr = yield meta
			for n in range(w):
				for meta in self.await_pos(self.offset(1,0)):
					self.curr = yield M_BOX_AFTER_S
		except NoSuchPosition: pass
		return
		
	def render(self):
		Pattern.render(self)
		return [
			Ellipse(a=(self.tl[0]+0.5,self.tl[1]+0.5),b=(self.br[0]+0.5,self.tl[1]+1.0+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID,fill=None,falpha=0.0),
			Line(a=(self.tl[0]+0.5,self.tl[1]+1.0),b=(self.tl[0]+0.5,self.br[1]), 
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.br[0]+0.5,self.tl[1]+1.0),b=(self.br[0]+0.5,self.br[1]), 
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Arc(a=(self.tl[0]+0.5,self.br[1]-1.0+0.5),b=(self.br[0]+0.5,self.br[1]+0.5),
				z=0, start=0.0, end=math.pi, stroke=C_FOREGROUND, salpha=1.0,
				w=1,stype=STROKE_SOLID,fill=None,falpha=0.0)	]
				

class RectangularBoxPattern(Pattern):
	
	tl = None
	br = None
	hs = None
	vs = None
	dashed = False
	
	def matcher(self):
		w,h = 0,0
		self.hs,self.vs = [],[]
		self.curr = yield
		self.tl = (self.curr.col,self.curr.row)
		rowstart = self.curr.col,self.curr.row
		lastvs,lasths = self.tl
		
		# top left corner
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_S|M_BOX_START_E)
		
		# top line 
		self.curr = yield self.expect("-",meta=M_OCCUPIED|M_BOX_START_S)
		if self.curr.char == " ": 
			# dashed box detection
			self.dashed = True
			self.curr = yield self.expect(" ",meta=M_OCCUPIED|M_BOX_START_S)
		while self.curr.char != "+":
			if self.dashed:
				self.curr = yield self.expect("-",meta=M_OCCUPIED|M_BOX_START_S)
				self.curr = yield self.expect(" ",meta=M_OCCUPIED|M_BOX_START_S)
			else:
				self.curr = yield self.expect("-",meta=M_OCCUPIED|M_BOX_START_S)
		w = self.curr.col-self.tl[0]+1
		
		# top right corner
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_S)
		self.curr = yield M_BOX_AFTER_E
		
		# next line
		for meta in self.await_pos(self.offset(0,1,rowstart)): 
			self.curr = yield meta
			
		# first content line left side
		rowstart = self.curr.col,self.curr.row
		self.curr = yield self.expect(";" if self.dashed else "|",meta=M_OCCUPIED|M_BOX_START_E)

		# first content line content
		for n in range(w-2):
			if( not self.occupied() and self.curr.char == "|"
					and self.curr.col-lastvs > 1 ):
				self.vs.append(self.curr.col)
				lastvs = self.curr.col
				self.curr = yield M_OCCUPIED
			else:
				self.curr = yield M_NONE
			if self.curr.char == "\n": self.reject()
			
		# first content line right side
		self.curr = yield self.expect(";" if self.dashed else "|",meta=M_OCCUPIED)
		self.curr = yield M_BOX_AFTER_E
			
		# next line
		for meta in self.await_pos(self.offset(0,1,rowstart)):
			self.curr = yield meta
			
		# middle section	
		while self.curr.char != "+":
		
			# left side
			rowstart = self.curr.col,self.curr.row
			self.curr = yield self.expect(";" if self.dashed else "|",meta=M_OCCUPIED|M_BOX_START_E)

			# content			
			if( not self.occupied() and self.curr.char == "-"
					and self.curr.row-lasths > 1 ):
				# horizontal separator
				self.hs.append(self.curr.row)
				lasths = self.curr.row
				for n in range(w-2):
					if self.curr.col in self.vs:
						self.curr = yield self.expect("-|",meta=M_OCCUPIED)
					else:
						self.curr = yield self.expect("-",meta=M_OCCUPIED)
			else:
				# non-separator
				for n in range(w-2):
					if self.curr.col in self.vs:
						self.curr = yield self.expect("|",meta=M_OCCUPIED)
					else:
						self.curr = yield M_NONE
					if self.curr.char == "\n": self.reject() 
			
			# right side
			self.curr = yield self.expect(";" if self.dashed else "|",meta=M_OCCUPIED)
			self.curr = yield M_BOX_AFTER_E
			
			# next line
			for meta in self.await_pos(self.offset(0,1,rowstart)):
				self.curr = yield meta
			
		# bottom left corner		
		rowstart = self.curr.col,self.curr.row
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_E)
		
		# bottom line
		if self.dashed:
			for n in range((w-2)/2):
				self.curr = yield self.expect("-",meta=M_OCCUPIED)
				self.curr = yield self.expect(" ",meta=M_OCCUPIED)
		else:
			for n in range(w-2):
				self.curr = yield self.expect("-",meta=M_OCCUPIED)
			
		# bottom right corner
		self.br = (self.curr.col,self.curr.row)
		self.curr = yield self.expect("+",meta=M_OCCUPIED)
		self.curr = yield M_BOX_AFTER_E
		
		# optional final line
		try:
			# next line
			for meta in self.await_pos(self.offset(0,1,rowstart)):
				self.curr = yield meta
				
			# area below box
			rowstart = self.curr.col,self.curr.row
			for n in range(w):
				if self.curr.char in ("\n",END_OF_INPUT): break
				self.curr = yield M_BOX_AFTER_S
				
		except NoSuchPosition: pass
		return
		
	def render(self):
		Pattern.render(self)
		retval = []
		if len(self.vs)>0 or len(self.hs)>0:
			if len(self.vs)>0 and len(self.hs)>0:
				fills = [[0.25,0.125],[0.125,0.0]]
			elif len(self.vs)>0:
				fills = [[0.25,0.0]]
			elif len(self.hs)>0:
				fills = [[0.25],[0.0]]
			secboundx = [self.tl[0]] + self.vs + [self.br[0]]
			secboundy = [self.tl[1]] + self.hs + [self.br[1]]
			for j in range(len(self.hs)+1):
				for i in range(len(self.vs)+1):
					falpha = fills[j%2][i%2]
					retval.append( Rectangle(a=(secboundx[i]+0.5,secboundy[j]+0.5),
						b=(secboundx[i+1]+0.5,secboundy[j+1]+0.5),z=-0.5,stroke=None,
						salpha=0.0,w=1,stype=STROKE_SOLID,fill=C_FOREGROUND,falpha=falpha) )
		retval.append( Rectangle(a=(self.tl[0]+0.5,self.tl[1]+0.5),
			b=(self.br[0]+0.5,self.br[1]+0.5),z=0,stroke=C_FOREGROUND,salpha=1.0,
			w=1,stype=STROKE_DASHED if self.dashed else STROKE_SOLID,fill=None,falpha=0.0) )
		return retval


class ParagmBoxPattern(Pattern):

	tl = None
	br = None
	dashed = False
	hs = None
	vs = None

	def matcher(self):
		w,h = 0,0
		self.hs,self.vs = [],[]
		self.curr = yield
		self.tl = (self.curr.col,self.curr.row)
		rowstart = self.curr.col,self.curr.row
		lastvs,lasths = self.tl
		
		# top left corner
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_S|M_BOX_START_E)
		
		# top line 
		self.curr = yield self.expect("-",meta=M_OCCUPIED|M_BOX_START_S)
		while self.curr.char != "+":
			self.curr = yield self.expect("-",meta=M_OCCUPIED|M_BOX_START_S)
		w = self.curr.col-self.tl[0]+1
		
		# top right corner
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_S)
		self.curr = yield M_BOX_AFTER_E
		
		# next line
		for meta in self.await_pos(self.offset(-1,1,rowstart)): 
			self.curr = yield meta
		
		while True:	
			# left side
			rowstart = self.curr.col,self.curr.row
			self.curr = yield self.expect("/",meta=M_OCCUPIED|M_BOX_START_E)

			# content
			for meta in self.await_pos(self.offset(w-1,0,rowstart)):
				self.curr = yield meta
				
			# right side
			self.curr = yield self.expect("/",meta=M_OCCUPIED)
			self.curr = yield M_BOX_AFTER_E
			
			# next line
			for meta in self.await_pos(self.offset(-1,1,rowstart)): 
				self.curr = yield meta
			
			if self.curr.char == "+": break
			
		# bottom left corner		
		rowstart = self.curr.col,self.curr.row
		self.curr = yield self.expect("+",meta=M_OCCUPIED|M_BOX_START_E)
		
		# bottom line
		for n in range(w-2):
			self.curr = yield self.expect("-",meta=M_OCCUPIED)
			
		# bottom right corner
		self.br = (self.curr.col,self.curr.row)
		self.curr = yield self.expect("+",meta=M_OCCUPIED)
		self.curr = yield M_BOX_AFTER_E
		
		# optional final line
		try:
			# next line
			for meta in self.await_pos(self.offset(0,1,rowstart)):
				self.curr = yield meta
				
			# area below box
			rowstart = self.curr.col,self.curr.row
			for n in range(w):
				if self.curr.char in ("\n",END_OF_INPUT): break
				self.curr = yield M_BOX_AFTER_S
				
		except NoSuchPosition: pass
		return
		
	def render(self):
		Pattern.render(self)
		h = self.br[1] - self.tl[1]
		w = self.br[0]+(h-1) - self.tl[0]
		return [
			Line(a=(self.tl[0]+0.5,self.tl[1]+0.5),b=(self.tl[0]+w+1+0.5,self.tl[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.tl[0]+0.5,self.tl[1]+0.5),b=(self.br[0]-w-1+0.5,self.br[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.br[0]-w-1+0.5,self.br[1]+0.5),b=(self.br[0]+0.5,self.br[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.tl[0]+w+1+0.5,self.tl[1]+0.5),b=(self.br[0]+0.5,self.br[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
		]
			
			
class LineSqCornerPattern(Pattern):

	pos = None
	ends = None
	
	def matcher(self):
		self.curr = yield
		if self.occupied(): self.reject()
		self.pos = self.curr.col,self.curr.row
		self.ends = []
		for m,dm,x,y in [
				(M_LINE_AFTER_E, M_DASH_AFTER_E, -1,0),
				(M_LINE_AFTER_S, M_DASH_AFTER_S, 0,-1),
				(M_LINE_AFTER_SE,M_DASH_AFTER_SE,-1,-1),
				(M_LINE_AFTER_SW,M_DASH_AFTER_SW,1,-1) ]:
			if self.curr.meta & m: 
				self.ends.append((x,y,bool(self.curr.meta & dm)))			
		self.curr = yield self.expect("+")
		for m,dm,x,y in [
				(M_LINE_START_E, M_DASH_START_E, 1,0),
				(M_LINE_START_SW,M_DASH_START_SW,-1,1),
				(M_LINE_START_S, M_DASH_START_S, 0,1),
				(M_LINE_START_SE,M_DASH_START_SE,1,1) ]:
			try:
				for meta in self.await_pos(self.offset(x,y,self.pos)):
					self.curr = yield meta
				if self.curr.meta & m:
					self.ends.append((x,y,bool(self.curr.meta & dm)))	
			except NoSuchPosition: pass
		if len(self.ends) < 2: self.reject()			
		return 
		
	def render(self):
		Pattern.render(self)
		centre = self.pos[0]+0.5,self.pos[1]+0.5
		retval = []
		for x,y,dsh in self.ends:
			retval.append( Line(a=centre,b=(centre[0]+x*0.5,centre[1]+y*0.5),
					z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
					stype=STROKE_DASHED if dsh else STROKE_SOLID) )
		return retval


class LineRdCornerPattern(Pattern):
	
	pos = None
	ends = None
	
	def matcher(self):
		self.curr = yield
		
		if self.occupied(): self.reject()
		
		self.pos = self.curr.col,self.curr.row
		
		up,down = False,False
		if self.curr.char == ".": 
			down = True
		elif self.curr.char == "'": 
			up = True
		elif self.curr.char == ":": 
			up,down = True,True
		else: self.reject()
		
		self.ends = []
		for m,dm,x,y in [ 
				(M_LINE_AFTER_E, M_DASH_AFTER_E, -1, 0),
				(M_LINE_AFTER_SW,M_DASH_AFTER_SW, 1,-1),
				(M_LINE_AFTER_S, M_DASH_AFTER_S,  0,-1),
				(M_LINE_AFTER_SE,M_DASH_AFTER_SE,-1,-1) ]:		
			if y < 0 and not up: continue
			if self.curr.meta & m: self.ends.append((x,y,self.curr.meta & dm))
			
		self.curr = yield M_OCCUPIED
		
		for m,dm,x,y in [
				(M_LINE_START_E, M_DASH_START_E,  1, 0),
				(M_LINE_START_SW,M_DASH_START_SW,-1, 1),
				(M_LINE_START_S, M_DASH_START_S,  0, 1),
				(M_LINE_START_SE,M_DASH_START_SE, 1, 1), ]:
			try:
				if y > 0 and not down: continue
				for meta in self.await_pos(self.offset(x,y,self.pos)):
					self.curr = yield meta
				if self.curr.meta & m: self.ends.append((x,y,self.curr.meta & dm))
			except NoSuchPosition: pass
		
		if len(self.ends) < 2: self.reject()
		return 
		
	def render(self):
		Pattern.render(self)
		centre = self.pos[0]+0.5,self.pos[1]+0.5
		retval = []
		rest = self.ends[:]
		while len(rest)>0:
			end = rest[0]
			rest = rest[1:]
			for oth in rest:
				a = centre[0]+end[0]*0.5, centre[1]+end[1]*0.5
				b = centre[0]+oth[0]*0.5, centre[1]+oth[1]*0.5
				retval.append( QuadCurve(a=a,b=b,c=centre,z=0,stroke=C_FOREGROUND,
					salpha=1.0,w=1,
					stype=STROKE_DASHED if end[2] and oth[2] else STROKE_SOLID) )		
		return retval


class ArrowheadPattern(Pattern):

	pos = None
	tobox = False
	dashed = False
	chars = None
	linemeta = None
	boxmeta = None
	dashmeta = None
	flipped = False
	xdir = None
	ydir = None
	
	def matcher(self):
		self.curr = yield
		self.pos = self.curr.col,self.curr.row
		if self.occupied() or not self.is_in(self.curr.char,self.chars): self.reject()
		if self.flipped:
			if self.curr.meta & self.boxmeta: self.tobox = True
		else:
			if not self.curr.meta & self.linemeta: self.reject()
			if self.curr.meta & self.dashmeta: self.dashed = True
		self.curr = yield M_OCCUPIED
		try:
			for meta in self.await_pos(self.offset(self.xdir-1,self.ydir)):
				self.curr = yield meta
			if self.flipped:
				if not self.curr.meta & self.linemeta: self.reject()
				if self.curr.meta & self.dashmeta: self.dashed = True
			else:
				if self.curr.meta & self.boxmeta: self.tobox = True	
		except NoSuchPosition:
			if self.flipped: raise
		return
		
	def render(self):
		Pattern.render(self)
		flip = -1 if self.flipped else 1
		centre = (self.pos[0]+0.5,self.pos[1]+0.5)
		spos = (centre[0]-0.5*self.xdir*flip,centre[1]-0.5*self.ydir*flip)
		apos2 = (centre[0]+(0.5+0.5*self.tobox)*self.xdir*flip,centre[1]+(0.5+0.5*self.tobox)*self.ydir*flip)
		apos1 = (apos2[0]-0.8*self.xdir*flip-0.5*self.ydir*flip,apos2[1]-0.8*self.ydir*flip/CHAR_H_RATIO-0.5*self.xdir*flip/CHAR_H_RATIO)
		apos3 = (apos2[0]-0.8*self.xdir*flip+0.5*self.ydir*flip,apos2[1]-0.8*self.ydir*flip/CHAR_H_RATIO+0.5*self.xdir*flip/CHAR_H_RATIO)
		return [
			Line(a=apos1,b=apos2,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=apos3,b=apos2,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=spos,b=apos2,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.dashed else STROKE_SOLID) ]
		

class LArrowheadPattern(ArrowheadPattern):

	chars = "<"
	linemeta = M_LINE_START_E
	boxmeta = M_BOX_AFTER_E
	dashmeta = M_DASH_START_E
	xdir = 1
	ydir = 0
	flipped = True
	
		
class RArrowheadPattern(ArrowheadPattern):
	
	chars = ">"
	linemeta = M_LINE_AFTER_E
	boxmeta = M_BOX_START_E
	dashmeta = M_DASH_AFTER_E
	xdir = 1
	ydir = 0
	flipped = False
	

class DArrowheadPattern(ArrowheadPattern):

	chars = "Vv"
	linemeta = M_LINE_AFTER_S
	boxmeta = M_BOX_START_S
	dashmeta = M_DASH_AFTER_S
	xdir = 0
	ydir = 1
	flipped = False
	# TODO: disallow word context


class UArrowheadPattern(ArrowheadPattern):
	
	chars = "^"
	linemeta = M_LINE_START_S
	boxmeta = M_BOX_AFTER_S
	dashmeta = M_DASH_START_S
	xdir = 0
	ydir = 1
	flipped = True

	
class CrowsFeetPattern(Pattern):

	pos = None
	xdir = 0
	ydir = 0
	chars = None
	startmeta = None
	endmeta = None
	flipped = True
	dashed = False

	def matcher(self):
		self.curr = yield
		self.pos = self.curr.col,self.curr.row
		if( self.occupied() or not self.is_in(self.curr.char,self.chars)
				or not self.curr.meta & self.startmeta ): 
			self.reject()
		if not self.flipped and self.curr.meta & self.dashmeta: 
			self.dashed = True
		self.curr = yield M_OCCUPIED
		for meta in self.await_pos(self.offset(self.xdir-1,self.ydir)):
			self.curr = yield meta
		if not self.curr.meta & self.endmeta: self.reject()
		if self.flipped and self.curr.meta & self.dashmeta:
			self.dashed = True
		return
		
	def render(self):
		Pattern.render(self)
		
		flip = -1 if self.flipped else 1
		centre = ( self.pos[0]+0.5, self.pos[1]+0.5 )
		spos = ( centre[0]-self.xdir*0.5*flip, centre[1]-self.ydir*0.5*flip )
		fpos1 = ( centre[0]+self.xdir*1.0*flip - 0.6*(not self.xdir),
					centre[1]+self.ydir*1.0*flip - 0.6*(not self.ydir)/CHAR_H_RATIO )
		fpos2 = ( centre[0]+self.xdir*1.0*flip, centre[1]+self.ydir*1.0*flip )
		fpos3 = ( centre[0]+self.xdir*1.0*flip + 0.6*(not self.xdir), 
					centre[1]+self.ydir*1.0*flip + 0.6*(not self.ydir)/CHAR_H_RATIO )
		fpos0 = ( fpos2[0]-self.xdir*1.0*flip, fpos2[1]-self.ydir*1.0*flip/CHAR_H_RATIO )
		return [ 
			Line(a=fpos0,b=fpos1,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=fpos0,b=fpos2,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=fpos0,b=fpos3,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=spos,b=fpos0,z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.dashed else STROKE_SOLID) ]

	
class LCrowsFeetPattern(CrowsFeetPattern):

	xdir = 1
	ydir = 0
	chars = ">"
	flipped = True
	startmeta = M_BOX_AFTER_E
	endmeta = M_LINE_START_E
	dashmeta = M_DASH_START_E


class RCrowsFeetPattern(CrowsFeetPattern):
	
	xdir = 1
	ydir = 0
	chars = "<"
	flipped = False
	startmeta = M_LINE_AFTER_E
	endmeta = M_BOX_START_E
	dashmeta = M_DASH_AFTER_E
	
	
class UCrowsFeetPattern(CrowsFeetPattern):

	xdir = 0
	ydir = 1
	chars = "Vv"
	flipped = True
	startmeta = M_BOX_AFTER_S
	endmeta = M_LINE_START_S
	dashmeta = M_DASH_START_S
	
	
class DCrowsFeetPattern(CrowsFeetPattern):

	xdir = 0
	ydir = 1
	chars = "^"
	flipped = False
	startmeta = M_LINE_AFTER_S
	endmeta = M_BOX_START_S
	dashmeta = M_DASH_AFTER_S


class ShortLinePattern(Pattern):
	
	xdir = 0
	ydir = 0
	char = None
	pos = None
	startmeta = None
	endmeta = None
	boxstartmeta = None
	boxendmeta = None
	frombox = False
	tobox = False
	stroketype = None

	def matcher(self):
		self.curr = yield
		if self.is_in(self.curr.char,TEXT_CHARS): self.reject()
		self.curr = yield M_NONE
		self.pos = self.curr.col,self.curr.row
		if self.curr.meta & self.boxstartmeta: self.frombox = True
		self.curr = yield self.expect(self.char,meta=M_OCCUPIED|self.startmeta)
		if self.is_in(self.curr.char,TEXT_CHARS): self.reject()
		try:
			for meta in self.await_pos(self.offset(self.xdir,self.ydir,self.pos)):
				self.curr = yield meta
			if self.curr.meta & self.boxendmeta: self.tobox = True
			if self.curr.char != END_OF_INPUT: yield self.endmeta
		except NoSuchPosition: pass
		return
		
	def render(self):
		Pattern.render(self)
		return [ Line(a=(self.pos[0]+0.5+self.xdir*-0.5+self.xdir*int(self.frombox)*-0.5,
						self.pos[1]+0.5+self.ydir*-0.5+self.ydir*int(self.frombox)*-0.5),
					b=(self.pos[0]+0.5+self.xdir*0.5+self.xdir*int(self.tobox)*0.5,
						self.pos[1]+0.5+self.ydir*0.5+self.ydir*int(self.tobox)*0.5),
					z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=self.stroketype) ]


class LongLinePattern(Pattern):

	xdir = 0	
	ydir = 0
	startchars = None
	midchars = None
	startpos = None
	endpos = None
	startmeta = None
	endmeta = None
	stroketype = None
	boxstartmeta = None
	boxendmeta = None
	frombox = False
	tobox = False
	
	def matcher(self):
		self.curr = yield
		pos = self.curr.col,self.curr.row
		self.startpos = pos
		if self.curr.meta & self.boxstartmeta: self.frombox = True
		self.curr = yield self.expect(self.startchars[0],meta=M_OCCUPIED|self.startmeta)
		for startchar in self.startchars[1:]:
			for meta in self.await_pos(self.offset(self.xdir,self.ydir,pos)):
				self.curr = yield meta
			pos = self.curr.col,self.curr.row
			self.curr = yield self.expect(startchar,meta=M_OCCUPIED)
		try:
			breaknow = False
			firsttime = True
			while not breaknow:
				for i,midchar in enumerate(self.midchars):
					for meta in self.await_pos(self.offset(self.xdir,self.ydir,pos)):
						self.curr = yield meta
					if( self.curr.char != midchar or self.occupied() 
							or self.curr.char == END_OF_INPUT ): 
						if i==0 and not firsttime: 
							breaknow = True
							break
						else:
							self.reject()
					pos = self.curr.col,self.curr.row
					self.curr = yield self.expect(midchar,meta=M_OCCUPIED)
				firsttime = False
			self.endpos = pos
			if self.curr.meta & self.boxendmeta: self.tobox = True
			if self.curr.char != END_OF_INPUT: yield self.endmeta
		except NoSuchPosition:
			if firsttime: self.reject()
			self.endpos = pos
		return
		
	def render(self):
		Pattern.render(self)
		return [ Line(a=(self.startpos[0]+0.5+self.xdir*-0.5+self.xdir*int(self.frombox)*-0.5,
						self.startpos[1]+0.5+self.ydir*-0.5+self.ydir*int(self.frombox)*-0.5),
					b=(self.endpos[0]+0.5+self.xdir*0.5+self.xdir*int(self.tobox)*0.5,
						self.endpos[1]+0.5+self.ydir*0.5+self.ydir*int(self.tobox)*0.5),
					z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=self.stroketype) ]
		
		
class ShortUpDiagLinePattern(ShortLinePattern):
	
	xdir = -1
	ydir = 1
	char = "/"
	startmeta = M_LINE_START_SW
	endmeta = M_LINE_AFTER_SW
	stroketype = STROKE_SOLID
	boxstartmeta = M_NONE
	boxendmeta = M_NONE


class LongUpDiagLinePattern(LongLinePattern):
	
	xdir = -1
	ydir = 1
	startchars = ["/"]
	midchars = startchars
	startmeta = M_LINE_START_SW
	endmeta = M_LINE_AFTER_SW
	stroketype = STROKE_SOLID
	boxstartmeta = M_NONE
	boxendmeta = M_NONE


class UpDiagDashedLinePattern(LongLinePattern):
	
	xdir = -1
	ydir = 1
	startchars = [","]
	midchars = startchars
	startmeta = M_LINE_START_SW | M_DASH_START_SW
	endmeta = M_LINE_AFTER_SW | M_DASH_AFTER_SW
	stroketype = STROKE_DASHED
	boxstartmeta = M_NONE
	boxendmeta = M_NONE
	
	
class ShortDownDiagLinePattern(ShortLinePattern):

	xdir = 1
	ydir = 1
	char = "\\"
	startmeta = M_LINE_START_SE
	endmeta = M_LINE_AFTER_SE
	stroketype = STROKE_SOLID
	boxstartmeta = M_NONE
	boxendmeta = M_NONE
	
		
class LongDownDiagLinePattern(LongLinePattern):

	xdir = 1
	ydir = 1
	startchars = ["\\"]
	midchars = startchars
	startmeta = M_LINE_START_SE
	endmeta = M_LINE_AFTER_SE
	stroketype = STROKE_SOLID
	boxstartmeta = M_NONE
	boxendmeta = M_NONE
	
		
class DownDiagDashedLinePattern(LongLinePattern):
	
	xdir = 1
	ydir = 1
	startchars = ["`"]
	midchars = startchars
	startmeta = M_LINE_START_SE | M_DASH_START_SE
	endmeta = M_LINE_AFTER_SE | M_DASH_AFTER_SE
	stroketype = STROKE_DASHED
	boxstartmeta = M_NONE
	boxendmeta = M_NONE
	
	
class ShortVertLinePattern(ShortLinePattern):

	xdir = 0
	ydir = 1
	char = "|"
	startmeta = M_LINE_START_S
	endmeta = M_LINE_AFTER_S
	stroketype = STROKE_SOLID
	boxstartmeta = M_BOX_AFTER_S
	boxendmeta = M_BOX_START_S
	
		
class LongVertLinePattern(LongLinePattern):

	xdir = 0
	ydir = 1
	startchars = ["|"]
	midchars = startchars
	startmeta = M_LINE_START_S
	endmeta = M_LINE_AFTER_S
	stroketype = STROKE_SOLID
	boxstartmeta = M_BOX_AFTER_S
	boxendmeta = M_BOX_START_S
	
	
class VertDashedLinePattern(LongLinePattern):

	xdir = 0
	ydir = 1
	startchars = [";"]
	midchars = startchars
	startmeta = M_LINE_START_S | M_DASH_START_S
	endmeta = M_LINE_AFTER_S | M_DASH_AFTER_S
	stroketype = STROKE_DASHED
	boxstartmeta = M_BOX_AFTER_S
	boxendmeta = M_BOX_START_S
	
	
class LongHorizLinePattern(LongLinePattern):

	xdir = 1
	ydir = 0
	startchars = ["-"]
	midchars = startchars
	startmeta = M_LINE_START_E
	endmeta = M_LINE_AFTER_E
	stroketype = STROKE_SOLID
	boxstartmeta = M_BOX_AFTER_E
	boxendmeta = M_BOX_START_E


class ShortHorizLinePattern(ShortLinePattern):
	
	xdir = 1
	ydir = 0
	char = "-"
	startmeta = M_LINE_START_E
	endmeta = M_LINE_AFTER_E
	stroketype = STROKE_SOLID
	boxstartmeta = M_BOX_AFTER_E
	boxendmeta = M_BOX_START_E


class HorizDashedLinePattern(LongLinePattern):
	
	xdir = 1
	ydir = 0
	startchars = ["-"," ","-"," "]
	midchars = ["-"," "]
	startmeta = M_LINE_START_E | M_DASH_START_E
	endmeta = M_LINE_AFTER_E | M_DASH_AFTER_E
	stroketype = STROKE_DASHED
	boxstartmeta = M_BOX_AFTER_E
	boxendmeta = M_BOX_START_E


class TinyCirclePattern(Pattern):

	pos = None
	
	def matcher(self):
		self.curr = yield
		if self.curr.char.isalpha(): self.reject()
		self.curr = yield M_NONE
		self.pos = self.curr.col,self.curr.row
		self.curr = yield self.expect("O")
		if self.curr.char.isalpha(): self.reject()
		return
		
	def render(self):
		Pattern.render(self)
		return [ Ellipse(a=(self.pos[0]+0.5-0.4,self.pos[1]+0.5-0.4/CHAR_H_RATIO), 
				b=(self.pos[0]+0.5+0.4,self.pos[1]+0.5+0.4/CHAR_H_RATIO), z=1, 
				stroke="magenta", salpha=1.0, w=1, stype=STROKE_SOLID, fill=None, falpha=0.0) ]
				
				
class SmallCirclePattern(Pattern):
	
	left = None
	right = None
	y = None
	
	def matcher(self):
		self.curr = yield
		self.left = self.curr.col
		self.y = self.curr.row
		self.curr = yield self.expect("(")
		for n in range(3):
			if self.curr.char == ")": break
			self.curr = yield M_NONE
		else:
			self.reject()
		self.right = self.curr.col
		self.curr = yield self.expect(")")
		return
		
	def render(self):
		Pattern.render(self)
		d = self.right-self.left
		return [ Ellipse(a=(self.left+0.5,self.y+0.5-d/2.0/CHAR_H_RATIO),
				b=(self.right+0.5,self.y+0.5+d/2.0/CHAR_H_RATIO), z=1, stroke="green",
				salpha=1.0, w=1, stype=STROKE_SOLID, fill=None, falpha=0.0) ]


class JumpPattern(Pattern):

	pos = None
	hdash = False
	vdash = False
	char = None

	def matcher(self):
		self.curr = yield
		ndash,edash,sdash,wdash = [False]*4
		if( self.curr.char != self.char or self.occupied() 
				or not self.curr.meta & M_LINE_AFTER_E 
				or not self.curr.meta & M_LINE_AFTER_S ):
			self.reject()
		if self.curr.meta & M_DASH_AFTER_E: wdash = True
		if self.curr.meta & M_DASH_AFTER_S: ndash = True
		self.pos = self.curr.col,self.curr.row
		self.curr = yield M_OCCUPIED
		for meta in self.await_pos(self.offset(1,0,self.pos)):
			self.curr = yield meta
		if not self.curr.meta & M_LINE_START_E: self.reject()
		if self.curr.meta & M_DASH_START_E: edash = True
		for meta in self.await_pos(self.offset(0,1,self.pos)):
			self.curr = yield meta
		if not self.curr.meta & M_LINE_START_S: self.reject()
		if self.curr.meta & M_DASH_START_S: sdash = True
		self.hdash = edash and wdash
		self.vdash = ndash and sdash 
		return
		
		
class LJumpPattern(JumpPattern):

	char = "("
		
	def render(self):
		JumpPattern.render(self)
		return [ 
			Line(a=(self.pos[0],self.pos[1]+0.5),b=(self.pos[0]+1.0,self.pos[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.hdash else STROKE_SOLID),
			Arc(a=(self.pos[0]+0.5-0.6,self.pos[1]),b=(self.pos[0]+0.5+0.6,self.pos[1]+1.0),
				z=0,start=math.pi*0.5,end=math.pi*1.5,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.vdash else STROKE_SOLID, fill=None,falpha=0.0), ]
	
	
class RJumpPattern(JumpPattern):

	char = ")"
	
	def render(self):
		JumpPattern.render(self)
		return [
			Line(a=(self.pos[0],self.pos[1]+0.5),b=(self.pos[0]+1.0,self.pos[1]+0.5),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.hdash else STROKE_SOLID),
			Arc(a=(self.pos[0]+0.5-0.6,self.pos[1]),b=(self.pos[0]+0.5+0.6,self.pos[1]+1.0),
				z=0,start=math.pi*-0.5,end=math.pi*0.5,stroke=C_FOREGROUND,salpha=1.0,
				w=1,stype=STROKE_DASHED if self.vdash else STROKE_SOLID,fill=None,falpha=0.0), ]
	
	
class UJumpPattern(JumpPattern):

	char = "^"
	
	def render(self):
		JumpPattern.render(self)
		return [
			Line(a=(self.pos[0]+0.5,self.pos[1]),b=(self.pos[0]+0.5,self.pos[1]+1.0),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.vdash else STROKE_SOLID),
			Arc(a=(self.pos[0],self.pos[1]+0.5-0.4),b=(self.pos[0]+1.0,self.pos[1]+0.5+0.4),
				z=0,start=math.pi,end=math.pi*2,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.hdash else STROKE_SOLID,fill=None,falpha=0.0), ]


class StickManPattern(Pattern):

	pos = None
	
	def matcher(self):
		self.curr = yield
		self.pos = self.curr.col,self.curr.row
		self.curr = yield self.expect("oO0")
		for meta in self.await_pos(self.offset(-2,1)):
			self.curr = yield meta
		self.curr = yield self.expect("-")
		self.curr = yield self.expect("|")
		self.curr = yield self.expect("-")
		for meta in self.await_pos(self.offset(-3,1)):
			self.curr = yield meta
		self.curr = yield self.expect("/")
		self.curr = yield self.expect(" ")
		self.curr = yield self.expect("\\")
		return
		
	def render(self):
		Pattern.render(self)
		return [
			Ellipse(a=self.offset(0,1-1.0/CHAR_H_RATIO,self.pos),b=self.offset(1,1,self.pos),
				z=0,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID,fill=None,falpha=0.0),
			Line(a=self.offset(0.5,1,self.pos),b=self.offset(0.5,1.8,self.pos),z=0,
				stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=self.offset(-1,1.25,self.pos),b=self.offset(2,1.25,self.pos),z=0,
				stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=self.offset(0.5,1.8,self.pos),b=self.offset(-0.5,2.8,self.pos),z=0,
				stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=self.offset(0.5,1.8,self.pos),b=self.offset(1.5,2.8,self.pos),z=0,
				stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID), ]


class DiamondBoxPattern(Pattern):

	top = None
	width = None

	def matcher(self):
		self.curr = yield
		
		# top peak
		self.top = self.curr.col,self.curr.row
		self.curr = yield self.expect(".",meta=M_OCCUPIED|M_BOX_START_E|M_BOX_START_S)
		apeak = self.curr.char=="'"
		if apeak:
			self.top = self.curr.col,self.curr.row
			self.curr = yield self.expect("'",meta=M_OCCUPIED|M_BOX_START_S)
			self.curr = yield self.expect(".",meta=M_OCCUPIED|M_BOX_START_S)
		self.curr = yield M_BOX_AFTER_E
		
		# top slope
		count = 1
		while True:
			try:
				for meta in self.await_pos(self.offset(-count*2-int(apeak),count,self.top)):
					self.curr = yield meta
				if self.occupied() or self.curr.char != ".":
					self.curr = yield M_NONE
					break
			except NoSuchPosition: break
			self.curr = yield self.expect(".",meta=M_OCCUPIED|M_BOX_START_E|M_BOX_START_S)
			self.curr = yield self.expect("'",meta=M_OCCUPIED|M_BOX_START_S)
			for meta in self.await_pos(self.offset((count-1)*2+1+int(apeak),count,self.top)):
				self.curr = yield meta
			self.curr = yield self.expect("'",meta=M_OCCUPIED|M_BOX_START_S)
			self.curr = yield self.expect(".",meta=M_OCCUPIED|M_BOX_START_S)
			self.curr = yield M_BOX_AFTER_E
			count += 1
		
		# middle
		for meta in self.await_pos(self.offset(-count*2-int(apeak)+1,count,self.top)):
			self.curr = yield meta
		self.width = 4*(count-1) + 3 + 2*int(apeak)
		self.curr = yield self.expect("<",meta=M_OCCUPIED|M_BOX_START_S|M_BOX_START_E)	
		for meta in self.await_pos(self.offset((count-1)*2+1+int(apeak),count,self.top)):
			self.curr = yield meta
		self.curr = yield self.expect(">",meta=M_OCCUPIED|M_BOX_START_S)
		self.curr = yield M_BOX_AFTER_E
		
		# bottom slope
		size = count
		for count in range(1,size):
			if count > 1:
				for meta in self.await_pos(self.offset(-(size-count)*2-int(apeak)-2,size+count,self.top)):
					self.curr = yield meta
				self.curr = yield M_BOX_AFTER_S
			for meta in self.await_pos(self.offset(-(size-count)*2-int(apeak)-1,size+count,self.top)):
				self.curr = yield meta
			self.curr = yield M_BOX_AFTER_S
			for meta in self.await_pos(self.offset(-(size-count)*2-int(apeak),size+count,self.top)):
				self.curr = yield meta
			self.curr = yield self.expect("'",meta=M_OCCUPIED|M_BOX_START_E)
			self.curr = yield self.expect(".",meta=M_OCCUPIED)
			for meta in self.await_pos(self.offset((size-count-1)*2+1+int(apeak),size+count,self.top)):
				self.curr = yield meta
			self.curr = yield self.expect(".",meta=M_OCCUPIED)
			self.curr = yield self.expect("'",meta=M_OCCUPIED)
			for meta in self.await_pos(self.offset((size-count-1)*2+1+int(apeak)+2,size+count,self.top)):
				self.curr = yield meta
			self.curr = yield M_BOX_AFTER_E | M_BOX_AFTER_S
			if count > 1:
				try:
					for meta in self.await_pos(self.offset((size-count-1)*2+1+int(apeak)+3,size+count,self.top)):
						self.curr = yield meta
					self.curr = yield M_BOX_AFTER_S
				except NoSuchPosition: pass
		count = size
		
		# bottom peak 	
		if count > 1:
			for meta in self.await_pos(self.offset(-int(apeak)-2,size*2,self.top)):
				self.curr = yield meta
			self.curr = yield M_BOX_AFTER_S
		for meta in self.await_pos(self.offset(-int(apeak)-1,size*2,self.top)):
			self.curr = yield meta
		self.curr = yield M_BOX_AFTER_S
		for meta in self.await_pos(self.offset(-int(apeak),size*2,self.top)):
			self.curr = yield meta
		self.curr = yield self.expect("'",meta=M_OCCUPIED|M_BOX_START_E)
		if apeak:
			self.curr = yield self.expect(".",meta=M_OCCUPIED)
			self.curr = yield self.expect("'",meta=M_OCCUPIED)
		for meta in self.await_pos(self.offset(int(apeak)+1,size*2,self.top)):
			self.curr = yield meta
		self.curr = yield M_BOX_AFTER_E | M_BOX_AFTER_S
		if count > 1:
			try:
				for meta in self.await_pos(self.offset(int(apeak)+2,size*2,self.top)):
					self.curr = yield meta
				self.curr = yield M_BOX_AFTER_S
			except NoSuchPosition: pass
		
		# optional final line
		try:
			if apeak:
				for i in range(3):
					for meta in self.await_pos(self.offset(-1+i,size*2+1,self.top)):
						self.curr = yield meta
					self.curr = yield M_BOX_AFTER_S
			else:
				for meta in self.await_pos(self.offset(0,size*2+1,self.top)):
					self.curr = yield meta
				self.curr = yield M_BOX_AFTER_S
		except NoSuchPosition: pass
		
		return
		
	def render(self):
		Pattern.render(self)
		apeak = (self.width-3)%4 == 2
		h = 3+2*((self.width-3-2*int(apeak))//4)
		return [
			Line(a=(self.top[0]+0.5,self.top[1]+0.5),
				b=(self.top[0]+0.5-self.width//2,self.top[1]+0.5+h//2),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.top[0]+0.5,self.top[1]+0.5),
				b=(self.top[0]+0.5+self.width//2,self.top[1]+0.5+h//2),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.top[0]+0.5-self.width//2,self.top[1]+0.5+h//2),	
				b=(self.top[0]+0.5,self.top[1]+0.5+h-1),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.top[0]+0.5+self.width//2,self.top[1]+0.5+h//2),
				b=(self.top[0]+0.5,self.top[1]+0.5+h-1),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID), ]


class UOutlineArrowheadPattern(Pattern):
	
	pos = None
	tobox = False
	dashed = False
	
	def matcher(self):
		self.curr = yield
		self.curr = yield self.expect("/")
		if self.curr.meta & M_BOX_AFTER_S: self.tobox = True
		self.pos = self.curr.col,self.curr.row
		self.curr = yield self.expect("_")
		self.curr = yield self.expect("\\")
		for meta in self.await_pos(self.offset(0,1,self.pos)):
			self.curr = yield meta
		if not (self.curr.meta & M_LINE_START_S): self.reject()
		if self.curr.meta & M_DASH_START_S: self.dashed = True
		return
	
	def render(self):
		Pattern.render(self)
		return [
			Line(a=(self.pos[0]+0.5,self.pos[1]-0.5*self.tobox),
				b=(self.pos[0],self.pos[1]+0.8/CHAR_H_RATIO-0.5*self.tobox),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.pos[0]+0.5,self.pos[1]-0.5*self.tobox),
				b=(self.pos[0]+1.0,self.pos[1]+0.8/CHAR_H_RATIO-0.5*self.tobox),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.pos[0],self.pos[1]+0.8/CHAR_H_RATIO-0.5*self.tobox),
				b=(self.pos[0]+1.0,self.pos[1]+0.8/CHAR_H_RATIO-0.5*self.tobox),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,stype=STROKE_SOLID),
			Line(a=(self.pos[0]+0.5,self.pos[1]+0.8/CHAR_H_RATIO-0.5*self.tobox),
				b=(self.pos[0]+0.5,self.pos[1]+1.0),
				z=1,stroke=C_FOREGROUND,salpha=1.0,w=1,
				stype=STROKE_DASHED if self.dashed else STROKE_SOLID), ]
	
	
class DOutlineArrowheadPattern(Pattern):
	pass
	

class LOutlineArrowheadPattern(Pattern):
	pass
	

class ROutlineArrowheadPattern(Pattern):
	pass
		
		
PATTERNS = [
	StickManPattern,			
	DbCylinderPattern,			
	DiamondBoxPattern,
	RectangularBoxPattern,					
	ParagmBoxPattern,
	#SmallCirclePattern,
	#TinyCirclePattern,
	#HorizDashedLinePattern,		
	LongHorizLinePattern,			
	LongVertLinePattern,			
	#VertDashedLinePattern,		
	LongUpDiagLinePattern,			
	#UpDiagDashedLinePattern,	
	LongDownDiagLinePattern,		
	#DownDiagDashedLinePattern,	
	UOutlineArrowheadPattern,
	ShortHorizLinePattern,
	ShortVertLinePattern,
	ShortUpDiagLinePattern,
	ShortDownDiagLinePattern,
	LineSqCornerPattern,		
	LineRdCornerPattern,		
	LJumpPattern,				
	RJumpPattern,				
	UJumpPattern,				
	LArrowheadPattern,			
	RArrowheadPattern,			
	DArrowheadPattern,			
	UArrowheadPattern,			
	LCrowsFeetPattern,			
	RCrowsFeetPattern,			
	UCrowsFeetPattern,			
	DCrowsFeetPattern,			
	LiteralPattern
]
