#!/usr/bin/env python3
import argparse,json,shutil,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"facts.json"; OUT=ROOT/"output"; VOICE=ROOT/"voices"; FPS=24
def run(c):
 try:
  p=subprocess.run(c,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  if c and "blender" in str(c[0]).lower():
   print("BLENDER STDOUT:",p.stdout[-5000:]); print("BLENDER STDERR:",p.stderr[-5000:])

 except subprocess.CalledProcessError as e:
  print("COMMAND FAILED:", " ".join(map(str,c)), file=sys.stderr)
  print(e.stdout or "", file=sys.stderr); print(e.stderr or "", file=sys.stderr); raise
def caption(text,path):
 im=Image.new("RGBA",(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(im); fp="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; f=ImageFont.truetype(fp,62) if Path(fp).exists() else ImageFont.load_default(); lines=[]; cur=""
 for word in text.split():
  test=(cur+" "+word).strip()
  if cur and d.textbbox((0,0),test,font=f)[2]>940: lines.append(cur); cur=word
  else: cur=test
 if cur: lines.append(cur)
 y=850-len(lines[:3])*42
 for line in lines[:3]:
  box=d.textbbox((0,0),line,font=f,stroke_width=5); x=(1080-(box[2]-box[0]))//2; d.text((x,y),line,font=f,fill="white",stroke_width=5,stroke_fill=(0,0,0,220)); y+=95
 im.save(path)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--episode-id",type=int); a=ap.parse_args(); episodes=json.loads(DATA.read_text(encoding="utf-8")); ep=next((e for e in episodes if int(e["id"])==a.episode_id),None) if a.episode_id else episodes[0]
 if ep is None: raise ValueError("Nie znaleziono odcinka")
 if len(ep["scenes"])<5 or len(ep["script"].split())<180: raise ValueError("Scenariusz musi mieć 180 słów i 5 scen.")
 blender=shutil.which("blender"); ffmpeg=shutil.which("ffmpeg"); ffprobe=shutil.which("ffprobe")
 if not all((blender,ffmpeg,ffprobe)): raise RuntimeError("Brakuje Blendera lub FFmpeg")
 OUT.mkdir(exist_ok=True); stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"); base=f"faktoryia_3d_{int(ep['id']):03d}_{stamp}"
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td); audio=tmp/"narration.wav"; run([sys.executable,"-m","piper","--data-dir",str(VOICE),"-m","pl_PL-darkman-medium","-f",str(audio),"--",ep["script"]]); pr=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)],capture_output=True,text=True,check=True); duration=float(pr.stdout.strip())
  if not 95<=duration<=155: raise ValueError(f"Lektor trwa {duration:.1f}s, wymagane 95–155s.")
  segdur=duration/len(ep["scenes"]); segments=[]
  for i,sc in enumerate(ep["scenes"]):
   prefix=tmp/f"s{i:02d}_"; run([blender,"--background","--threads","2","--python",str(ROOT/"src"/"render_3d.py"),"--","--scene-index",str(i),"--output",str(prefix)]); frames=sorted(tmp.glob(f"s{i:02d}_*.png"))
   print("RENDERED FILES:", [p.name for p in tmp.iterdir() if p.suffix==".png"][:12], "COUNT:", len(frames));
   if len(frames)<20: raise RuntimeError(f"Renderowanie sceny {i+1} nie powiodło się.")
   raw=tmp/f"raw{i:02d}.mp4"; run([ffmpeg,"-y","-hide_banner","-loglevel","error","-framerate",str(FPS),"-start_number","1","-i",str(prefix)+"_%04d.png","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p",str(raw)])
   cap=tmp/f"cap{i:02d}.png"; caption(sc["caption"],cap); seg=tmp/f"seg{i:02d}.mp4"; run([ffmpeg,"-y","-hide_banner","-loglevel","error","-stream_loop","-1","-i",str(raw),"-i",str(cap),"-t",f"{segdur:.3f}","-filter_complex","[0:v]scale=1080:1920:flags=lanczos[bg];[bg][1:v]overlay=0:0:format=auto[v]","-map","[v]","-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(seg)]); segments.append(seg)
  concat=tmp/"concat.txt"; concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments),encoding="utf-8"); silent=tmp/"silent.mp4"; run([ffmpeg,"-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)]); run([ffmpeg,"-y","-hide_banner","-loglevel","error","-i",str(silent),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-t",f"{duration:.3f}","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT/(base+".mp4"))])
 desc=f"{ep['title']}\n\n{ep.get('description','')}\n\nŹRÓDŁA:\n"+"\n".join("- "+s for s in ep["sources"])+"\n\n#cogdyby #nauka #ciekawostki\n"; (OUT/(base+"_opis.txt")).write_text(desc,encoding="utf-8"); print(f"Gotowy film 3D: {OUT/(base+'.mp4')} ({duration:.1f}s)")
if __name__=="__main__": main()
