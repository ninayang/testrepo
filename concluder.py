import logging
from google.appengine.ext import ndb
from point import point
from Utils import Utils

class concluder():
  needs_concluding=[] # A vector of vectors of points. 
                      # Each inner vector starts with a 
                      # low down point. The next oint is its superpoint, etc and so the inner vec
                      # contains all the ancestors of its first point in order from bottom to top.
                      # The last point in an inner vector is either a point with no superpoint,
                      # or a point that is already in the needs_concluding in some other inner vector.
                      # thus the last point in an inner vector could well be in some other inner vector.
  conc_info=[]  #a list of lists. The inner lists are all 4 elts, 
                #point_to_concnclude id
                #the point to conclude title, 
                # old conc
                # new conc
                #the first inner list in the outer list represents the first conc concluded.
                #When a new conc is the same as its old conc, we stop concluding up
                #and just that last one is in the list.
  
  def __init__(self):
    self.needs_concluding = []
    self.conc_info=[]
    return None
  
  def conclude_all_needs_concluding(self):
    """returns conc_info array of changed conclusions info"""
    error_message = ""
    for iteration_count in xrange(1000):
      if iteration_count == 999:
        error_message = "Failed to conclude all the points that depend on this point because there's too many, possibly due to a circularity with use_conclusion."
        break
      else:
        point_to_conclude = self.find_point_to_conclude()  
        if point_to_conclude == None: # normal, all points concluded termination
          break
        elif point_to_conclude == "error":
          error_message = "Could not conclude all the points that depend on this point, probably due to a circularity with use_conclusion."
          break
        else: 
          """The idea of testing that the new conclusion is equal to the prev conc and therefore we can stop
            concluding all the ancestors of the point is clever BUT, both editing a point and
            points with attribute subpoints, in the case where the conclude method returns
            the source point (as in numbers, often pros and perhaps others) means that
            the before and after concs are eq but NOT the same as some fields have been munged like value and title
            and maybe others. we could: 
            1. copy the orig conc, then test it against the new one but
            what if we have lots of subpoints to copy? means making lots of copies.
            2. Have conclude methods NEVER return its source point,
            but that means making new points for conclusions.
            3.  stop doing the point_equal trick which is easiest to implement and be confident that
               its right so that's what I'm doing. Need to optimize subpoint_anal to make that faster.
           <set orig_conclusion=point_to_conclude.<get_conclusion/>>
             point_to_conclude.<conclude_etc/>
              <if> point_to_conclude.<get_conclusion/>.<point_equal orig_conclusion /> <!-- 
                       Beware, orig_conclusion will be false when conclude_all_needs_concluding is called
                       from conclude_down during a discussion load. That's ok but make it be the arg to point_equal,
                       not the subject!
                       if this is true, it meant we really didn't need to conclude this point after all
                        because it just concluded to the same thing, but we couldn't have known that until we concluded it.
                        But now that we know that, there was no real reason to have it or its ancestor on the list
                        anyway, so just get rid of them all and pretend they were never on the list in the first place.
                       -->
                    .<remove_point_and_ancestors point_to_conclude/>
                  else    .<remove_point point_to_conclude/>
              </if>
            </set>""" 
          logging.info("in canc with title: " +  point_to_conclude.title + " spkey: " + str(point_to_conclude.superpoint_key))  
          
          old_conc_key = point_to_conclude.conclusion_key
          old_conc = None
          old_conc_type_and_subtype_name = "None"

          logging.info("in concluder old_conc_key: " + str(old_conc_key))
      

         old_conc = old_conc_key.get() #beware,this can be None since we might have deleted that point from the db earlier in this conclude_up cycle
         if old_conc != None: #needs work: now we won't have a good old_conc_type to show user
           old_conc_type_and_subtype_name = old_conc.type_and_subtype_name()
          #klude fix for save new point duplicate point row in browser, etc
          if old_conc_key != None: # ie we don't have a new point_to_conclude which has never had a conclusions
             old_conc = old_conc_key.get()
             old_conc_type_and_subtype_name = old_conc.type_and_subtype_name()
          new_conc = point_to_conclude.conclude_etc()
          logging.info("in canc after conclude_etc title: " +  point_to_conclude.title + " spkey: " + str(point_to_conclude.superpoint_key))  
          
          self.conc_info.append({"id": point_to_conclude.to_id(), 
                                 "title": point_to_conclude.title, 
                                 "old_conc_type_and_subtype_name": old_conc_type_and_subtype_name, 
                                 "new_conc_type_and_subtype_name": new_conc.type_and_subtype_name(),
                                 "point_row_conclusion_html":      new_conc.point_row_conclusion_html()
                                 }) 
          if new_conc.key == old_conc_key:
            self.remove_point_and_ancestors(point_to_conclude)
          else:
            self.remove_point(point_to_conclude)
          logging.info("in canc bot of loop title: " +  point_to_conclude.title + " spkey: " + str(point_to_conclude.superpoint_key)) #has key 
         
    if error_message != "":
      """now we must do what conclude_etc and conc_info_append does above, only making up our own conclusion error point"""
      logging.info("canc got eror mes: " + error_message) #not reached
      new_conc = point.fix.error_nu(title=error_message,
                                    description= "unconcluded points: " + a_concluder.needs_concluding_to_string(),
                                    broken_point_key = self.key) 
      point_to_conclude.conclude_etc_aux(new_conc)
      old_conc_key = point_to_conclude.conclusion_key
      old_conc = None
      old_conc_type_and_subtype_name = "None"
      if old_conc_key != None: # ie we don't have a new point_to_conclude which has never had a conclusions
        old_conc = old_conc_key.get()
        old_conc_type_and_subtype_name = old_conc.type_and_subtype_name()      
      self.conc_info = ([{"id": point_to_conclude.to_id(), 
                          "title": point_to_conclude.title, 
                          "old_conc_type_and_subtype_name": old_conc_type_and_subtype_name, 
                          "new_conc_type_and_subtype_name": new_conc.type_and_subtype_name(),
                          "point_row_conclusion_html":      new_conc.point_row_conclusion_html()
                        }]) 
    return self.conc_info

  def find_point_to_conclude(self):
    """returns 
       - next point to conclude or 
       - None meaning no points left to conclude or 
       - "error" in which case we've got a circularity error. 
    """
    if len(self.needs_concluding) == 0: # normal, everything OK termination
      return None    
    for value in self.needs_concluding:
      a_head_point = value[0]
      if self.point_is_not_non_head_point(a_head_point): #ie a_head_point  is not ALSO in another inner vec as a non-head point
        if isinstance(a_head_point, point.meta.use_conclusion):       
          if self.already_in(a_head_point.id_to_point(a_head_point.uses_id)):
            pass
          else:
            return a_head_point
        else:
          return a_head_point
    return "error" # there are point's left in needs_concluing but none appropriate to conclude next.

  def point_is_not_non_head_point(self, a_point):
    """returns true if a_point is good to conclude, false if its a non_first point in an inner vec """
    for outer_value in self.needs_concluding:
      for index in range(len(outer_value)):
        inner_value = outer_value[index]
        if inner_value == a_point:
          if index == 0:
            break #we're good for this inner vec, check next inner vec 
          else:
            return False
    return True

  def needs_concluding_to_string(self):
    """for an error message"""
    result = "<ul>"
    for value in self.needs_concluding:
      for value in value:
        result += "<li>" +  value.title + "</li>"
    return result + "</ul>"
 
  def remove_point(self, a_point):
    """a_point better be the first point in at least 1 inner vec or error.
      assume its never a 2nd thru nth point in an inner vec,
      but might be in more than 1 inner vec."""
    removed_at_least_once = False
    orig_max_index = len(self.needs_concluding) - 1
    for value in range(orig_max_index + 1):
      inner_key = orig_max_index - value
      inner_vec = self.needs_concluding[inner_key]
      if a_point == inner_vec[0]:
        if len(inner_vec) == 1:
          self.needs_concluding.remove(inner_vec)
        else:
          inner_vec.remove(a_point)
        removed_at_least_once = True
    if not(removed_at_least_once):
      error("in remove_point, couldn't find: " + a_point.title + " to remove from needs_concluding.")

  def add_to_inner_vec(self, inner_vec, a_point):
    """returning True means no more points in this line to be added. 
       False means there might still be more ancestors to add."""
    if self.already_in(a_point):
      inner_vec.append(a_point)
      return True
    else:
      inner_vec.append(a_point)
      return False

  def already_in(self, a_point):
    for value in self.needs_concluding:
      for value in value:
        if value == a_point:
          return True
    return False

  def add_to_needs_concluding(self, a_point):
    """ after calling add_to_needs_concluding, needs_concluding will look like    
       <v <v c b a discussion1/>
          <v g f discussion1/>
          <v x y b/>
       />
      note that after an ancestor line finds an item already in, it includes that item but stops the line
      as in the last one, "b" is in the first line so dont put b's ancestors in a 2nd time.
      we never have folders, the "highest' ancestor is always the discussion that we're in.
    """
    if self.already_in(a_point):
      return None
    else:
      if Utils.has_attr(a_point, "used_by"):
        for value in a_point.used_by:
          self.add_to_needs_concluding(value)
      inner_vec = [a_point]
      # now go up the hierarchy, adding as need be 
      superp = a_point
      for value in range(100):
        superp = superp.get_superpoint()
        if superp == None:
          break
        elif self.add_to_inner_vec(inner_vec, superp):
          break
        elif value == 99:
          error("shouldnt in add_to_needs_concluding reached 100 with starting point: " + a_point.title)
      self.needs_concluding.append(inner_vec)
      
  def remove_point_and_ancestors(self, a_point):
    removed_at_least_once = False
    orig_max_index = len(self.needs_concluding) - 1
    for index in range(orig_max_index + 1):
      inner_key = orig_max_index - index
      inner_vec = self.needs_concluding[inner_key]
      if a_point == inner_vec[0]:
        self.needs_concluding.remove(inner_vec)
        removed_at_least_once = True
    if not(removed_at_least_once):
      error("in remove_point_and_ancestors, couldn't find: " + a_point.title + " to remove from needs_concluding.")
