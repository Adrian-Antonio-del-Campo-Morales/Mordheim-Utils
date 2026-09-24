import ts from 'typescript';
import fs from 'node:fs';
import path from 'node:path';
const config=ts.readConfigFile('tsconfig.json',ts.sys.readFile);
const parsed=ts.parseJsonConfigFileContent(config.config,ts.sys,process.cwd());
const program=ts.createProgram(parsed.fileNames,parsed.options), checker=program.getTypeChecker();
const rows=[];
for(const file of program.getSourceFiles()){
 if(!file.fileName.includes('/src/') && !file.fileName.includes('\\src\\')) continue;
 if(!file.fileName.endsWith('.tsx')||file.fileName.includes('.test.'))continue;
 const sinks=[];
 function leaf(n){
  if(ts.isJsxElement(n)||ts.isJsxSelfClosingElement(n)||ts.isJsxFragment(n))return;
  if(ts.isConditionalExpression(n)){leaf(n.whenTrue);leaf(n.whenFalse);return;}
  if(ts.isBinaryExpression(n)&&n.operatorToken.kind===ts.SyntaxKind.AmpersandAmpersandToken){leaf(n.right);return;}
  if(ts.isCallExpression(n)&&ts.isPropertyAccessExpression(n.expression)&&n.expression.name.text==='map')return;
  if(ts.isCallExpression(n)&&n.expression.getText(file)==='presentationOutput')return;
  if([ts.SyntaxKind.NullKeyword,ts.SyntaxKind.FalseKeyword,ts.SyntaxKind.TrueKeyword].includes(n.kind)||n.getText(file)==='undefined')return;
  const type=checker.getTypeAtLocation(n);
  const safe=t=> t.isUnion()?t.types.every(safe):checker.getPropertiesOfType(t).some(p=>/(uiTextBrand|formattedTextBrand|resolvedTextBrand|enumTextBrand)/.test(p.name));
  sinks.push({line:file.getLineAndCharacterOfPosition(n.getStart(file)).line+1,expression:n.getText(file),type:checker.typeToString(type),ready:safe(type)});
 }
 function visit(n){
  if(ts.isJsxText(n)&&n.text.trim())sinks.push({line:file.getLineAndCharacterOfPosition(n.getStart(file)).line+1,expression:n.text,ready:false});
  if(ts.isJsxExpression(n)&&n.expression&&(!ts.isJsxAttribute(n.parent)||['title','alt','placeholder','aria-label','aria-description','data-label','data-tooltip','data-disabled-reason','label'].includes(n.parent.name.text)))leaf(n.expression);
  ts.forEachChild(n,visit);
 }
 visit(file);
 if(sinks.length) rows.push({file:path.relative(process.cwd(),file.fileName),ready:sinks.filter(s=>s.ready).length,remaining:sinks.filter(s=>!s.ready).length,sinks});
}
fs.writeFileSync('../../build/generated/presentation-remaining.json',JSON.stringify(rows,null,2));
console.log(rows.map(({file,ready,remaining})=>({file,ready,remaining})).sort((a,b)=>a.remaining-b.remaining));
