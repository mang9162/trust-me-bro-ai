var _dragged=null;
function _isAnc(anc,el){var c=el;while(c){if(c===anc)return true;c=c.parentElement;}return false;}
function _clearDrop(){document.querySelectorAll('.fn-item').forEach(function(i){i.classList.remove('drop-before','drop-inside','drop-after');});var t=document.querySelector('.fn-tree');if(t)t.classList.remove('drag-over');}
function _getPos(e,nodeEl){var r=nodeEl.getBoundingClientRect(),y=e.clientY-r.top,h=r.height;return y<h*0.3?'before':y>h*0.7?'after':'inside';}
function initFnDnD(){
  var tree=document.querySelector('.fn-tree');if(!tree)return;
  function setupItem(item){
    item.setAttribute('draggable','true');
    item.addEventListener('dragstart',function(e){e.stopPropagation();_dragged=item;e.dataTransfer.effectAllowed='move';setTimeout(function(){item.classList.add('dragging');},0);});
    item.addEventListener('dragend',function(){item.classList.remove('dragging');_clearDrop();_dragged=null;});
    var node=item.querySelector(':scope > .fn-node');if(!node)return;
    if(!node.querySelector('.fn-delete')){var del=document.createElement('button');del.className='fn-delete';del.textContent='×';del.title='Remove from tree';del.onclick=function(e){e.stopPropagation();item.remove();};node.appendChild(del);}
    node.addEventListener('dragover',function(e){if(!_dragged||_dragged===item||_isAnc(_dragged,item))return;e.preventDefault();e.stopPropagation();_clearDrop();_getPos(e,node);item.classList.add('drop-'+_getPos(e,node));});
    node.addEventListener('dragleave',function(e){if(!node.contains(e.relatedTarget))item.classList.remove('drop-before','drop-inside','drop-after');});
    node.addEventListener('drop',function(e){e.preventDefault();e.stopPropagation();_clearDrop();if(!_dragged||_dragged===item||_isAnc(_dragged,item))return;var pos=_getPos(e,node),parent=item.parentElement;if(pos==='before')parent.insertBefore(_dragged,item);else if(pos==='after')parent.insertBefore(_dragged,item.nextElementSibling);else{var ch=item.querySelector(':scope > .fn-children');if(ch)ch.appendChild(_dragged);}});
  }
  tree.addEventListener('dragover',function(e){if(!_dragged||e.target!==tree)return;e.preventDefault();_clearDrop();tree.classList.add('drag-over');});
  tree.addEventListener('drop',function(e){if(e.target!==tree)return;e.preventDefault();_clearDrop();if(_dragged)tree.appendChild(_dragged);});
  document.querySelectorAll('.fn-item').forEach(setupItem);
}
function copyFnTree(){var tree=document.querySelector('.fn-tree');if(!tree)return;navigator.clipboard.writeText(tree.outerHTML).then(function(){var el=document.getElementById('fn-copy-confirm');if(el){el.style.display='inline';setTimeout(function(){el.style.display='none';},2500);}});}
initFnDnD();
function activateFn(el,taskIds){
  var isAlreadyActive=el.classList.contains('fn-active');
  document.querySelectorAll('.fn-node').forEach(function(n){n.classList.remove('fn-active');});
  document.querySelectorAll('details.task-card').forEach(function(c){c.classList.remove('highlighted');});
  if(isAlreadyActive)return;
  el.classList.add('fn-active');
  taskIds.forEach(function(id){document.querySelectorAll('.task-id').forEach(function(tid){if(tid.textContent.trim()===id){var card=tid.closest('details.task-card');if(card){card.classList.add('highlighted');card.open=true;}}});});
  var first=document.querySelector('details.task-card.highlighted');if(first)first.scrollIntoView({behavior:'smooth',block:'center'});
}
function activateStep(n){
  var box=document.querySelector('.flow-box[data-step="'+n+'"]');
  var isAlreadyActive=box&&box.classList.contains('active');
  document.querySelectorAll('.flow-box').forEach(function(b){b.classList.remove('active');});
  document.querySelectorAll('details.task-card').forEach(function(c){c.classList.remove('highlighted');});
  if(isAlreadyActive)return;
  if(box)box.classList.add('active');
  document.querySelectorAll('details.task-card').forEach(function(card){var s=card.dataset.step;if(s==='all'||s===String(n))card.classList.add('highlighted');});
  var target=document.querySelector('details.task-card[data-step="'+n+'"]');
  if(target){target.open=true;target.scrollIntoView({behavior:'smooth',block:'center'});}
}