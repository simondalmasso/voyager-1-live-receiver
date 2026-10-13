export async function ready(page,path='/'){
  await page.goto(path);
  await page.waitForFunction(()=>{
    const audit=window.__order013?.getAudit?.();
    return audit?.commonEpochFrame===true&&typeof audit.truth==='string'&&audit.truth!=='LOADING';
  },null,{timeout:25000});
}
