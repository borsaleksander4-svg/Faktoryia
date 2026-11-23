import bpy, math, sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
idx=int(args[args.index("--scene-index")+1]); prefix=args[args.index("--output")+1]
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def mat(n,c,r=.7):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*c,1); m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=r; return m
def cube(n,l,s,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=l); o=bpy.context.object; o.name=n; o.dimensions=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m); return o
def ball(n,l,s,m,v=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=v,ring_count=8,radius=1,location=l); o=bpy.context.object; o.name=n; o.scale=s; o.data.materials.append(m); return o
def person(x,y,coat,skin):
 cube("Character body",(x,y,1.15),(.42,.3,.7),coat); ball("Character head",(x,y,1.68),(.19,.19,.22),skin)
 for side in (-1,1):
  bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.075,depth=.65,location=(x+side*.12,y,.43)); o=bpy.context.object; o.data.materials.append(coat); o.rotation_euler[1]=side*.12; o.keyframe_insert(data_path="rotation_euler",frame=1); o.rotation_euler[1]=-side*.12; o.keyframe_insert(data_path="rotation_euler",frame=48)
ground=mat("Ground",(.12,.18,.22)); road=mat("Road",(.035,.05,.07)); concrete=mat("Concrete",(.32,.38,.43)); water=mat("Water",(.015,.18,.34),.25); ice=mat("Ice",(.65,.86,.96),.2); snow=mat("Snow",(.92,.96,1)); yellow=mat("Windows",(.95,.63,.25),.3); red=mat("Red coat",(.55,.08,.07)); skin=mat("Skin",(.7,.43,.28)); green=mat("Tree",(.08,.25,.14))
cube("Ground",(0,0,-.3),(18,18,.5),ground); cube("Road",(0,-2,-.02),(18,2.4,.08),road)
for x in (-5,-2.5,0,2.5,5):
 h=3+(int(abs(x))%3)*.55; cube("Apartment",(x,3,h/2),(1.8,1.8,h),concrete)
 for z in (1,2,3):
  for dx in (-.45,.45): cube("Window",(x+dx,2.06,z),(.34,.025,.42),yellow)
for x in (-4,4):
 bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=.75,radius2=0,depth=1.7,location=(x,1,1.7)); bpy.context.object.data.materials.append(green)
person(-1,-2.6,red,skin); person(1,-2.2,ground,skin)
bpy.ops.object.camera_add(location=(7.5,-12,6.5)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.lens=43; bpy.context.scene.camera=cam
cam.location.x-=.25; cam.keyframe_insert(data_path="location",frame=1); cam.location.x+=.5; cam.keyframe_insert(data_path="location",frame=48)
bpy.ops.object.light_add(type="AREA",location=(0,-4,8)); light=bpy.context.object; light.data.energy=1500; light.data.shape="DISK"; light.data.size=7; light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat("-Z","Y").to_euler()
if idx==1:
 cube("Waterfront",(0,-4,.03),(16,7,.14),water)
 for i in range(16):
  x=-6+(i%4)*4; y=-6+(i//4)*1.5; o=ball("Forming ice",(x,y,.2),(1.15,.15,.7),ice,8); o.keyframe_insert(data_path="scale",frame=1); o.scale=(1.6,.23,1); o.keyframe_insert(data_path="scale",frame=48)
elif idx==2:
 cube("Frozen sea",(0,-3,0),(18,13,.2),water)
 for i in range(30):
  x=((i*37)%130)/10-6.5; y=-8+((i*19)%100)/10; o=ball("Ice floe",(x,y,.2),(1+(i%3)*.2,.12,.7),ice,7); o.rotation_euler[2]=i*.4; o.keyframe_insert(data_path="rotation_euler",frame=1); o.rotation_euler[2]+=.18; o.keyframe_insert(data_path="rotation_euler",frame=48)
elif idx==3:
 for o in list(bpy.data.objects):
  if o.name=="Apartment": o.data.materials.clear(); o.data.materials.append(ice)
 cube("Snowy street",(0,-2,.1),(18,2.5,.16),snow)
 for i in range(50):
  x=((i*17)%140)/10-7; y=((i*29)%120)/10-6; o=ball("Snowfall",(x,y,3+(i%5)*.5),(.04,.04,.04),snow,6); o.keyframe_insert(data_path="location",frame=1); o.location.z-=1.2; o.keyframe_insert(data_path="location",frame=48)
elif idx==4:
 cube("Frozen square",(0,-1,.1),(9,7,.2),snow)
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=1.5,depth=.45,location=(0,-1,.4)); bpy.context.object.data.materials.append(ice)
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.3,depth=1.6,location=(0,-1,1.35)); bpy.context.object.data.materials.append(ice)
 person(-2,-3,red,skin); person(2,-3,ground,skin)
elif idx>=5:
 earth=ball("Frozen Earth",(0,0,1.7),(2.8,2.8,2.8),water,32)
 for i in range(10):
  a=i*math.tau/10; ball("Ice cap",(math.cos(a)*1.7,math.sin(a)*1.7,3),(.8,.45,.2),ice,8)
 earth.keyframe_insert(data_path="rotation_euler",frame=1); earth.rotation_euler[2]=math.tau; earth.keyframe_insert(data_path="rotation_euler",frame=48)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=480; scene.render.resolution_y=854; scene.render.resolution_percentage=100; scene.render.fps=12; scene.frame_start=1; scene.frame_end=48; scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGB"; scene.world.color=(.025,.045,.08); scene.render.filepath=prefix+"_"; scene.frame_set(1); bpy.ops.render.render(animation=True)
