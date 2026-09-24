import ts from 'typescript';
import fs from 'node:fs';
import path from 'node:path';
const config=ts.readConfigFile('tsconfig.json',ts.sys.readFile);
const parsed=ts.parseJsonConfigFileContent(config.config,ts.sys,process.cwd());
const program=ts.createProgram(parsed.fileNames,parsed.options), checker=program.getTypeChecker();
for(const name of process.argv.slice(2)) {
 const file=program.getSourceFile(path.resolve(name)); const edits=[];const helpers=new Set();
 function safe(type){return type.isUnion()?type.types.every(safe):checker.getPropertiesOfType(type).some(p=>/(uiTextBrand|formattedTextBrand|resolvedTextBrand|enumTextBrand|catalogueTextBrand)/.test(p.name));}
 function wrap(expr){
  if(ts.isCallExpression(expr)&&expr.expression.getText(file)==='presentationOutput')return;
  const type=checker.getTypeAtLocation(expr); const code=expr.getText(file);let text;
  if(safe(type))text=`presentationOutput(${code})`;
  else if(type.flags & ts.TypeFlags.NumberLike){text=`presentationOutput(textNumber(${code}, locale))`;helpers.add('textNumber');}
  else if(type.isUnion()&&type.types.some(t=>t.flags&ts.TypeFlags.Undefined)&&type.types.every(t=>(t.flags&ts.TypeFlags.Undefined)||safe(t)))text=`(${code}) === undefined ? undefined : presentationOutput((${code})!)`;
  else if(ts.isConditionalExpression(expr)){wrap(expr.whenTrue);wrap(expr.whenFalse);return;}
  else if(ts.isParenthesizedExpression(expr)){wrap(expr.expression);return;}
  if(text)edits.push({start:expr.getStart(file),end:expr.end,text});
 }
 function visit(n){
  if(ts.isJsxText(n)&&[':', '#', '×'].includes(n.text.trim())) {helpers.add('textSymbol'); edits.push({start:n.getStart(file),end:n.end,text:` {presentationOutput(textSymbol(${JSON.stringify(n.text.trim())}))} `});}
  if(ts.isJsxExpression(n)&&n.expression&&(!ts.isJsxAttribute(n.parent)||['title','alt','placeholder','aria-label','aria-description','data-label','data-tooltip','data-disabled-reason'].includes(n.parent.name.text)))wrap(n.expression);
  ts.forEachChild(n,visit);
 }
 visit(file);let source=file.text;
 for(const e of edits.sort((a,b)=>b.start-a.start))source=source.slice(0,e.start)+e.text+source.slice(e.end);
 for(const helper of helpers){
  const imports=file.statements.filter(ts.isImportDeclaration).some(st=>st.importClause?.namedBindings && ts.isNamedImports(st.importClause.namedBindings)&&st.importClause.namedBindings.elements.some(b=>b.name.text===helper));
  if(!imports)source=`import { ${helper} } from "../campaign/presentation-values";\n`+source;
 }
 fs.writeFileSync(name,source); console.log(name,edits.length);
}
