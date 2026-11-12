/** @param {object} task Canonical numeric question. @param {string} value User answer. @returns {boolean} Pure exact comparison after outer whitespace removal; no evaluation. */
export function checkAnswer(task,value){return typeof value==='string' && value.trim()===task.answer;}
/** @param {Array<[string,string,number]>} edges Directed nonnegative weighted edges. @param {string} start Start vertex. @param {string} end Target vertex. @returns {{distance:number,path:string[]}} Dijkstra result, Infinity and empty path when unreachable. No effects; rejects invalid weights. */
export function shortestPath(edges,start,end){
 const nodes=new Set([start,end]);for(const [a,b,w] of edges){if(!Number.isFinite(w)||w<0)throw new RangeError('Nonnegative finite weight required');nodes.add(a);nodes.add(b);}
 const distance=new Map([...nodes].map(n=>[n,Infinity])),parent=new Map(),remaining=new Set(nodes);distance.set(start,0);
 while(remaining.size){let v=null;for(const n of remaining)if(v===null||distance.get(n)<distance.get(v))v=n;
  if(distance.get(v)===Infinity)break;remaining.delete(v);if(v===end)break;
  for(const [a,b,w] of edges)if(a===v&&remaining.has(b)&&distance.get(v)+w<distance.get(b)){distance.set(b,distance.get(v)+w);parent.set(b,v);}
 }
 if(distance.get(end)===Infinity)return {distance:Infinity,path:[]};
 const route=[end];while(route[0]!==start)route.unshift(parent.get(route[0]));return {distance:distance.get(end),path:route};
}
