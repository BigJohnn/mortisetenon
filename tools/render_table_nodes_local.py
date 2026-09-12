#!/usr/bin/env python3
"""Derive local DRAFT GLB animation and software renders from checked STL.

Requires trimesh, numpy and Pillow. No Blender or GPU is needed.
Geometry is unchanged; STL mm convert once to glTF metres / Y-up.
"""
from pathlib import Path
import json
import struct
import numpy as np
import trimesh
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"cad/table-node-pair_local-check"
COLORS={"Leg":(0.73,0.42,0.27),"Apron":(0.84,0.65,0.40),"Top":(0.73,0.76,0.71)}


def animated_glb(parts, target):
    scene=trimesh.Scene()
    rotation=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
    for name,mesh in parts.items():
        mesh=mesh.copy()
        mesh.apply_scale(0.001)
        mesh.apply_transform(rotation)
        mesh.visual.face_colors=np.array([*COLORS[name],1])*255
        scene.add_geometry(mesh,node_name=name,geom_name=name)
    raw=scene.export(file_type="glb")
    json_length=struct.unpack_from("<I",raw,12)[0]
    data=json.loads(raw[20:20+json_length])
    binary=bytearray(raw[28+json_length:])
    data["asset"]["extras"]={"source":"Independent local CAD check, not an Onshape export","evidence_state":"DRAFT","length_unit":"m","up_axis":"Y","mm_to_m_applied_once":True}
    def accessor(values,kind):
        array=np.array(values,dtype="<f4")
        binary.extend(b"\0"*((-len(binary))%4))
        view=len(data["bufferViews"])
        data["bufferViews"].append({"buffer":0,"byteOffset":len(binary),"byteLength":array.nbytes})
        binary.extend(array.tobytes())
        index=len(data["accessors"])
        bounds=array.reshape(len(array),-1)
        data["accessors"].append({"bufferView":view,"componentType":5126,"count":len(array),"type":kind,"min":bounds.min(axis=0).tolist(),"max":bounds.max(axis=0).tolist()})
        return index
    time=accessor([0,1.2,2.4],"SCALAR")
    animation={"name":"Explode","channels":[],"samplers":[]}
    for name,heights in [("Top",[0,0.096,0.096]),("Apron",[0,0,0.048])]:
        node=next(i for i,n in enumerate(data["nodes"]) if n.get("name")==name)
        data["nodes"][node].pop("matrix",None)
        data["nodes"][node]["translation"]=[0,0,0]
        output=accessor([[0,h,0] for h in heights],"VEC3")
        animation["channels"].append({"sampler":len(animation["samplers"]),"target":{"node":node,"path":"translation"}})
        animation["samplers"].append({"input":time,"output":output,"interpolation":"LINEAR"})
    data["animations"]=[animation]
    data["buffers"][0]["byteLength"]=len(binary)
    encoded=json.dumps(data,separators=(",",":")).encode()
    encoded+=b" "*((-len(encoded))%4)
    binary.extend(b"\0"*((-len(binary))%4))
    glb=struct.pack("<4sII",b"glTF",2,12+8+len(encoded)+8+len(binary))+struct.pack("<I4s",len(encoded),b"JSON")+encoded+struct.pack("<I4s",len(binary),b"BIN\0")+binary
    target.write_bytes(glb)
    loaded=trimesh.load(str(target),force="scene")
    assert len(loaded.geometry)==3
    assert np.allclose(loaded.bounds,[[-.048,-.096,-.020],[.048,.016,.020]],atol=1e-7)


def render(parts, target, exploded):
    # Orthographic triangle rasterizer with a real depth buffer. Painter sorting
    # can incorrectly expose blind mortises through the top face of the panel.
    size=1600
    pixels=np.empty((size,size,3),dtype=np.uint8);pixels[:]=[238,234,225]
    depth=np.full((size,size),-np.inf)
    az,el=np.radians([-54,22])
    eye=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.array([-np.sin(az),np.cos(az),0])
    up=np.cross(eye,right)
    scale=size/255
    light=np.array([.3,-.5,.8]);light/=np.linalg.norm(light)
    for name,mesh in parts.items():
        offset=96 if name=="Top" else 48 if name=="Apron" else 0
        triangles=mesh.triangles.copy()
        if exploded:triangles[:,:,2]+=offset
        lighting=.62+.38*np.maximum(mesh.face_normals@light,0)
        colors=np.array(COLORS[name])[None,:]*lighting[:,None]*255
        for vertices,colour in zip(triangles,colors):
            vertices=vertices-[0,0,8]
            points=np.column_stack([size/2+scale*(vertices@right),size/2-scale*(vertices@up)])
            z=vertices@eye
            low=np.maximum(np.floor(points.min(axis=0)).astype(int),0)
            high=np.minimum(np.ceil(points.max(axis=0)).astype(int)+1,size)
            x0,y0=low;x1,y1=high
            if x1<=x0 or y1<=y0:continue
            (a,b),(c,d),(e,f)=points
            denominator=(d-f)*(a-e)+(e-c)*(b-f)
            if abs(denominator)<1e-10:continue
            yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
            w0=((d-f)*(xx-e)+(e-c)*(yy-f))/denominator
            w1=((f-b)*(xx-e)+(a-e)*(yy-f))/denominator
            w2=1-w0-w1
            zz=w0*z[0]+w1*z[1]+w2*z[2]
            visible=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(zz>depth[y0:y1,x0:x1])
            depth[y0:y1,x0:x1][visible]=zz[visible]
            pixels[y0:y1,x0:x1][visible]=colour.astype(np.uint8)
    Image.fromarray(pixels).resize((1200,1200),Image.Resampling.LANCZOS).save(target,quality=95)


def main():
    for slug in ["clamp-tenon","shouldered-tenon"]:
        parts={name:trimesh.load(str(OUTPUT/f"{slug}_{name}.stl"),force="mesh") for name in COLORS}
        animated_glb(parts,OUTPUT/f"{slug}_preview.glb")
        for label,exploded in [("assembled",False),("exploded",True)]:
            render(parts,OUTPUT/f"{slug}_{label}.webp",exploded)
        print(slug,"GLB (3 parts, 1 ordered animation, metre bounds checked) and two renders generated")


if __name__=="__main__":main()
