import bpy, math, sys, random
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
idx=int(a[a.index("--scene-index")+1]); prefix=a[a.index("--output")+1]; random.seed(idx+12)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def M(n,c,rough=.48,metal=0):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*c,1); p.inputs["Roughness"].default_value=rough; p.inputs["Metallic"].default_value=metal
 return m
ice=M("Glacier cyan",(.48,.83,.96)); snow=M("Snow",(.92,.97,1)); ocean=M("Deep ocean",(.015,.12,.25)); blue=M("Sea blue",(.04,.35,.57)); dark=M("Midnight",(.035,.08,.16)); wall=M("Buildings",(.19,.3,.42)); window=M("Warm windows",(1,.58,.18)); red=M("Rescue orange",(.95,.2,.08)); skin=M("Skin",(.62,.36,.23)); green=M("Pine",(.035,.23,.15)); land=M("Land",(.12,.37,.25)); cloud=M("Cloud",(.78,.88,.97)); yellow=M("Sun",(1,.65,.2)); fish=M("Fish",(.98,.48,.08))
def cube(n,p,s,m,b=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object; o.name=n; o.dimensions=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
 if b: mod=o.modifiers.new("Rounded edges","BEVEL"); mod.width=b; mod.segments=2
 return o
def ball(n,p,s,m,v=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=v,ring_count=8,radius=1,location=p); o=bpy.context.object; o.name=n; o.scale=s; o.data.materials.append(m); return o
def cone(n,p,r,d,m,v=8):
 bpy.ops.mesh.primitive_cone_add(vertices=v,radius1=r,radius2=0,depth=d,location=p); bpy.context.object.data.materials.append(m); return bpy.context.object
def animate(o,p1,p2):
 o.location=p1; o.keyframe_insert(data_path="location",frame=1); o.location=p2; o.keyframe_insert(data_path="location",frame=48)
def human(x,y,coat):
 ball("Head",(x,y,1.38),(.22,.22,.24),skin)
 cube("Winter coat",(x,y,.82),(.55,.34,.72),coat,.07)
 cube("Scarf",(x,y-.2,1.02),(.6,.06,.12),red,.02)
 for s in (-1,1):
  cube("Leg",(x+s*.14,y,.25),(.14,.16,.5),dark,.025)
  arm=cube("Arm",(x+s*.35,y,.83),(.14,.16,.58),coat,.03); arm.rotation_euler[1]=s*.25
 cyl=cone("Winter hat",(x,y,1.62),.25,.25,red,12)
def tree(x,y):
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.08,depth=.8,location=(x,y,.4)); bpy.context.object.data.materials.append(dark)
 for z,r in ((.9,.55),(1.35,.4),(1.7,.25)): cone("Snowy pine",(x,y,z),r,.9,green,8)
cube("Display plinth",(0,0,-.5),(15,15,.5),dark)
if idx==0:
 cube("Street",(0,-1,0),(12,7,.16),wall)
 cube("Frozen roadway",(0,-2,.13),(12,2.4,.1),ice)
 for x in (-4.5,-2.2,0,2.2,4.5):
  h=3.5+(int(abs(x)*2)%3)*.5; cube("City block",(x,2,h/2),(1.8,1.5,h),wall,.08)
  for z in (1,2,3):
   for dx in (-.45,.45): cube("Lit window",(x+dx,1.22,z),(.36,.035,.4),window,.02)
  cube("Snowy rooftop",(x,2,h+.08),(1.9,1.6,.14),snow,.04)
 for x in (-5.2,5.2): tree(x,.1)
 human(-1.2,-2.4,red); human(1.1,-2.1,dark)
 for i in range(20):
  x=random.uniform(-5,5); y=random.uniform(-3,3); shard=ball("Ice spreading",(x,y,.28),(.12,.08,.12),ice,8); shard.keyframe_insert(data_path="scale",frame=1); shard.scale=(.7,.16,.35); shard.keyframe_insert(data_path="scale",frame=48)
elif idx==1:
 cube("Ocean",(0,0,-.1),(13,12,.2),ocean)
 for i in range(35):
  x=random.uniform(-5.5,5.5); y=random.uniform(-5,5); f=ball("Sea ice floe",(x,y,.15),(random.uniform(.45,1),random.uniform(.3,.7),.13),ice if i%2 else snow,8); animate(f,(x,y,.15),(x+random.uniform(-.2,.2),y,.18))
 hull=cube("Icebreaker hull",(0,-.5,.65),(3.5,.85,.7),red,.18); cube("Ship deck",(0,-.5,1.1),(2.8,.7,.15),snow,.04); cube("Bridge",(.45,-.5,1.5),(.9,.65,.75),snow,.05)
 for x in (.2,.55,.8): cube("Bridge window",(x,-.84,1.58),(.18,.025,.2),blue,.01)
 cube("Mast",(-.8,-.5,1.8),(.06,.06,1.1),dark)
elif idx==2:
 for i in range(8):
  x=-5+i*1.4; z=3+random.random()*1.4
  for j in range(5): ball("Frozen cloud",(x+(j-2)*.28,1,z),(.48,.36,.3),cloud,12)
 for i in range(60):
  x=random.uniform(-5.5,5.5); y=random.uniform(-3,3); z=random.uniform(1,5); flake=ball("Falling snow",(x,y,z),(.045,.045,.045),snow,6); animate(flake,(x,y,z),(x+.25,y-.3,z-1.8))
elif idx==3:
 globe=ball("Planet Earth",(0,0,2),(2.8,2.8,2.8),blue,48)
 for x,y,sx,sy in ((-.9,2.2,.7,.85),(.6,2.4,.7,.5),(1.25,1.6,.4,.7),(-1.4,1.3,.35,.5),(0,1,.55,.4)):
  o=ball("Continents",(x,y,2),(sx,sy,.08),land); o.rotation_euler[1]=-.3
 for z in (4.65,-.65): ball("Polar ice cap",(0,0,z),(1.65,1.65,.2),snow,32)
 globe.rotation_euler=(.12,0,-.2); globe.keyframe_insert(data_path="rotation_euler",frame=1); globe.rotation_euler.z=.4; globe.keyframe_insert(data_path="rotation_euler",frame=48)
 ball("Sun",(3.7,1,4.5),(.6,.6,.6),yellow,24)
elif idx==4:
 cube("Frozen lake",(0,0,0),(12,9,.25),ocean)
 cube("Thick transparent ice",(0,0,.2),(11.8,8.8,.22),ice,.1)
 for i in range(7):
  x=-4+i*1.3; y=random.uniform(-2,2); f=ball("Fish trapped below ice",(x,y,.08),(.3,.12,.1),fish,12); animate(f,(x,y,.08),(x+.15,y,.08))
 for x in (-4.5,4.5): tree(x,2)
 human(0,-3,red)
 for i in range(18):
  c=cube("Ice fracture",(random.uniform(-4,4),random.uniform(-2.5,2.5),.34),(.8,.025,.015),snow); c.rotation_euler.z=random.random()*3
elif idx==5:
 cube("Snowfield",(0,0,0),(13,10,.3),snow)
 for x in (-5,-3,3,5): tree(x,2)
 cube("Emergency shelter",(0,0,1.15),(3.6,2.5,2.3),wall,.1)
 for s in (-1,1):
  roof=cube("Shelter roof",(s*.85,0,2.42),(2,2.8,.18),dark,.04); roof.rotation_euler.y=s*.43
 cube("Door",(0,-1.28,.85),(.65,.08,1.5),red,.04)
 for x in (-1,1): cube("Warm window",(x,-1.3,1.55),(.5,.04,.52),window,.03)
 for x in (-2.8,2.8): human(x,-1.6,red)
 for i in range(25):
  x=random.uniform(-5,5); y=random.uniform(-3,3); z=random.uniform(2,5); f=ball("Snowfall",(x,y,z),(.04,.04,.04),snow,6); animate(f,(x,y,z),(x+.2,y,z-2))
bpy.ops.object.camera_add(location=(8,-15,9)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.type="ORTHO"; cam.data.ortho_scale=12.8; bpy.context.scene.camera=cam
cam.keyframe_insert(data_path="location",frame=1); cam.location.x=7.3; cam.keyframe_insert(data_path="location",frame=48)
bpy.ops.object.light_add(type="AREA",location=(1,-8,11)); l=bpy.context.object; l.data.energy=1800; l.data.shape="DISK"; l.data.size=8; l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat("-Z","Y").to_euler()
s=bpy.context.scene; s.render.engine="BLENDER_WORKBENCH"; s.display.shading.color_type="MATERIAL"; s.display.shading.light="STUDIO"; s.display.shading.show_shadows=True; s.display.shading.show_cavity=True; s.display.shading.cavity_type="WORLD"; s.display.shading.background_type="WORLD"; s.display.shading.background_color=(.018,.035,.07); s.render.resolution_x=900; s.render.resolution_y=1600; s.render.resolution_percentage=100; s.render.fps=24; s.frame_start=1; s.frame_end=48; s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"; s.render.film_transparent=False; s.view_settings.view_transform="AgX"; s.view_settings.look="AgX - Medium High Contrast"; s.view_settings.exposure=0; s.view_settings.gamma=1; s.world.use_nodes=True; s.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.018,.035,.07,1); s.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.32;  s.render.use_file_extension=False
for frame in range(1,49):
 s.frame_set(frame); s.render.filepath=prefix+"_"+f"{frame:04d}.png"; bpy.ops.render.render(write_still=True)
