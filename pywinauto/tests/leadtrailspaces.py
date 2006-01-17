# GUI Application automation and testing library
# Copyright (C) 2006 Mark Mc Mahon
#
# This library is free software; you can redistribute it and/or 
# modify it under the terms of the GNU Lesser General Public License 
# as published by the Free Software Foundation; either version 2.1 
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public 
# License along with this library; if not, write to the 
#    Free Software Foundation, Inc.,
#    59 Temple Place,
#    Suite 330, 
#    Boston, MA 02111-1307 USA 

testname = "LeadTrailSpaces"
def LeadTrailSpacesTest(windows):
	bugs = []
	for win in windows:	
		if not win.ref:
			continue
		
		locLeadSpaces = GetLeadSpaces(win.Text)
		locTrailSpaces = GetTrailSpaces(win.Text)

		refLeadSpaces = GetLeadSpaces(win.ref.Text)
		refTrailSpaces = GetTrailSpaces(win.ref.Text)
		
		diffs = []
		if locLeadSpaces != refLeadSpaces:
			diffs.append("Leading", locLeadSpaces, locTrailSpaces)

		if locTrailSpaces != refTrailSpaces:
			diffs.append("Trailing", locTrailSpaces, refTrailSpaces)
		
		for diff, loc, ref in diffs:
			bugs.append((
				[win, ],
				{
					"Lead-Trail": diff,
					"Ref": ref,
					"Loc": loc,
				},
				testname,
				0,)
			)
	return bugs


def GetLeadSpaces(title):
	spaces = ''
		
	for i in range(0, len(title)):
		if not title[i].isspace():
			break
		
		spaces += title[i]
		
	return spaces
		
		
def GetTrailSpaces(title):
	rev = "".join(reversed(title))
	spaces = GetLeadSpaces(rev)
	return "".join(reversed(spaces))


LeadTrailSpacesTest.TestsMenus = True	
