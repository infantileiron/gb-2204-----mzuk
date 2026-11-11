import type {Point,Candidate} from '../types/entities';
export function projection(points:Point[],candidates:Candidate[]){
const all=[...points,...candidates];const ref=all[0]?.longitude||0;
const unwrap=(lon:number)=>ref+((lon-ref+540)%360)-180;
const xs=all.map(p=>unwrap(p.longitude)),ys=all.map(p=>p.latitude);
const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
const centerLat=(minY+maxY)/2,cos=Math.max(.01,Math.cos(centerLat*Math.PI/180));
const lonKm=111.195*cos,latKm=111.195;
const scale=Math.min(690/Math.max(2,(maxX-minX)*lonKm),390/Math.max(2,(maxY-minY)*latKm));
return{x:(lon:number)=>400+(unwrap(lon)-(minX+maxX)/2)*lonKm*scale,y:(lat:number)=>260-(lat-centerLat)*latKm*scale,radius:(km:number)=>km*scale,centerLat};
}
