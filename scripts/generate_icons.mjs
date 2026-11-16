// Rebuild with: node scripts/generate_icons.mjs (no external dependencies).
import { mkdir, writeFile } from 'node:fs/promises';
import { deflateSync } from 'node:zlib';

const output = new URL('../static/icons/', import.meta.url);
const colors = { background: [67,56,202], white: [255,255,255], lavender: [199,210,254], mint: [94,234,212] };
const bars = [
    { x:144, y:240, w:48, h:104, r:16, color:'lavender' },
    { x:224, y:200, w:48, h:144, r:16, color:'white' },
    { x:304, y:160, w:48, h:184, r:16, color:'mint' }
];
const star = [[172,140],[180,164],[204,172],[180,180],[172,204],[164,180],[140,172],[164,164]];
function rounded(x,y,b) {
    if (x<b.x || y<b.y || x>b.x+b.w || y>b.y+b.h) return false;
    const dx=x-Math.max(b.x+b.r,Math.min(x,b.x+b.w-b.r));
    const dy=y-Math.max(b.y+b.r,Math.min(y,b.y+b.h-b.r));
    return dx*dx+dy*dy <= b.r*b.r;
}
function polygon(x,y) {
    let inside=false;
    for (let i=0,j=star.length-1;i<star.length;j=i++) {
        const [xi,yi]=star[i], [xj,yj]=star[j];
        if (((yi>y)!==(yj>y)) && x<(xj-xi)*(y-yi)/(yj-yi)+xi) inside=!inside;
    }
    return inside;
}
const crcTable=Array.from({length:256},(_,n)=>{
    for(let k=0;k<8;k++) n=(n&1)?0xedb88320^(n>>>1):n>>>1;
    return n>>>0;
});
function chunk(type,data) {
    const name=Buffer.from(type), bytes=Buffer.concat([name,data]);
    let crc=0xffffffff;
    for(const value of bytes) crc=crcTable[(crc^value)&255]^(crc>>>8);
    const header=Buffer.alloc(4), tail=Buffer.alloc(4);
    header.writeUInt32BE(data.length); tail.writeUInt32BE((crc^0xffffffff)>>>0);
    return Buffer.concat([header,bytes,tail]);
}
function png(size,maskable=false) {
    const raw=Buffer.alloc((size*4+1)*size), samples=4;
    for(let y=0;y<size;y++) for(let x=0;x<size;x++) {
        const sum=[0,0,0]; let alpha=0;
        for(let sy=0;sy<samples;sy++) for(let sx=0;sx<samples;sx++) {
            const px=(x+(sx+.5)/samples)*512/size, py=(y+(sy+.5)/samples)*512/size;
            if(!maskable && !rounded(px,py,{x:0,y:0,w:512,h:512,r:112})) continue;
            let color=colors.background;
            for(const bar of bars) if(rounded(px,py,bar)) color=colors[bar.color];
            if(polygon(px,py)) color=colors.white;
            for(let c=0;c<3;c++) sum[c]+=color[c];
            alpha++;
        }
        const offset=y*(size*4+1)+1+x*4;
        for(let c=0;c<3;c++) raw[offset+c]=alpha?Math.round(sum[c]/alpha):0;
        raw[offset+3]=Math.round(alpha*255/(samples*samples));
    }
    const header=Buffer.alloc(13);
    header.writeUInt32BE(size,0); header.writeUInt32BE(size,4); header[8]=8; header[9]=6;
    return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),
        chunk('IDAT',deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);
}
await mkdir(output,{recursive:true});
const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">\n'
    + '<rect width="512" height="512" rx="112" fill="#4338ca"/>\n'
    + bars.map(b=>'<rect x="'+b.x+'" y="'+b.y+'" width="'+b.w+'" height="'+b.h+'" rx="'+b.r
        +'" fill="rgb('+colors[b.color].join(',')+')"/>').join('\n')
    + '\n<polygon points="'+star.map(p=>p.join(',')).join(' ')+'" fill="white"/>\n</svg>\n';
await writeFile(new URL('app-icon.svg',output),svg);
for(const size of [192,512]) await writeFile(new URL('icon-'+size+'.png',output),png(size));
await writeFile(new URL('icon-maskable-512.png',output),png(512,true));
await writeFile(new URL('apple-touch-icon.png',output),png(180,true));
const sizes=[16,32,48], images=sizes.map(size=>png(size));
const ico=Buffer.alloc(6+16*sizes.length); ico.writeUInt16LE(1,2); ico.writeUInt16LE(sizes.length,4);
let offset=ico.length;
images.forEach((data,i)=>{
    const at=6+i*16; ico[at]=sizes[i]; ico[at+1]=sizes[i];
    ico.writeUInt16LE(1,at+4); ico.writeUInt16LE(32,at+6);
    ico.writeUInt32LE(data.length,at+8); ico.writeUInt32LE(offset,at+12); offset+=data.length;
});
await writeFile(new URL('favicon.ico',output),Buffer.concat([ico,...images]));
// Keep legacy installed-app icon URLs working.
for (const size of [192,512]) await writeFile(new URL('../icon-'+size+'.png',output),png(size));
console.log('Generated SVG, PNG, maskable, Apple touch, ICO and legacy assets.');
