// Self-contained demonstrator. No imported personal implementation or historical training data.
export function verify(data){
 if(data?.meta?.data_class!=="synthetic")throw Error("Only synthetic samples are admitted");
 if(!Array.isArray(data.studies)||data.studies.length<2||!Array.isArray(data.branches))throw Error("Incomplete study inventory");
 if(new Set(data.studies.map(s=>s.id)).size!==data.studies.length)throw Error("Duplicate study");
 for(const s of data.studies){
  if(!/^E-\d+$/.test(s.id)||!s.question||!s.method||!s.limits||!s.horizon||!s.title)throw Error("Incomplete study contract");
  const n=s.probabilities?.length;
  if(!n||n<3||s.issued?.length!==n||s.outcomes?.length!==n||!(s.baseline>=0&&s.baseline<=1))throw Error("Invalid observations");
  if(s.probabilities.some(p=>typeof p!=="number"||!Number.isFinite(p)||p<0||p>1))throw Error("Invalid probabilities");
  if(s.outcomes.some(y=>y!==0&&y!==1))throw Error("Invalid outcomes");
 }
 if(new Set(data.branches.map(b=>b.id)).size!==data.branches.length)throw Error("Duplicate branch");
 const sum=data.branches.reduce((a,b)=>a+b.weight,0);
 if(data.branches.some(b=>!b.name||!b.mechanism||!b.watch||typeof b.weight!=="number"||b.weight<0)||Math.abs(sum-1)>1e-9)throw Error("Scenario weights must sum to 1");
 return true;
}
export function brier(p,y){if(!p?.length||p.length!==y?.length)throw Error("Invalid evaluation");return p.reduce((sum,x,i)=>sum+(x-y[i])**2,0)/p.length;}
export function score(study){
 const error=brier(study.probabilities,study.outcomes);
 const baselineError=brier(study.probabilities.map(()=>study.baseline),study.outcomes);
 return {n:study.outcomes.length,brier:error,baselineBrier:baselineError,skill:baselineError>0?1-error/baselineError:null,coverage:1};
}
export function calibration(study){
 return study.probabilities.map((p,i)=>({issued:study.issued[i],p,y:study.outcomes[i]}));
}
