import { host } from '@hermes/plugin-sdk';
import { useState } from 'react';
import { jsx } from 'react/jsx-runtime';

async function draft(text) {
  const ok = await host.composer.insertText(null, text, { mode: 'block' });
  host.notify({ kind: ok ? 'info' : 'warning', message: ok ? 'Đã thêm yêu cầu vào ô chat; kiểm tra rồi nhấn Gửi. Chưa gọi browser.' : 'Không tìm thấy ô chat đang mở; mở phiên chat trước.' });
}

function submit(text) {
  const session = host.state?.focusedSessionId?.get();
  if (!session || typeof host.composer.submit !== 'function') {
    host.notify({kind:'warning',message:'Cần phiên chat đang mở và SDK composer.submit. Không chạy ngầm hoặc gửi sang phiên khác.'});
    return false;
  }
  if (host.state.busyBySession?.get()?.[session]) {
    host.notify({kind:'info',message:'Phiên đang thực hiện. Không gửi trùng yêu cầu DMS.'});
    return false;
  }
  const sent = host.composer.submit(session, text);
  host.notify({kind:sent?'info':'warning',message:sent?'Đã gửi yêu cầu DMS; không cần nhấn Gửi thêm.':'Không có composer hiển thị của phiên này; chưa thực hiện.'});
  return sent;
}

function Panel() {
  const [work, setWork] = useState('');
  const [query, setQuery] = useState('');
  const [url, setUrl] = useState('');
  const [filename, setFilename] = useState('');
  const [output, setOutput] = useState('');
  const validWork = /^[A-Za-z0-9_-]{1,64}$/.test(work);
  const validUrl = /^https:\/\/dms\.newtecons\.vn(?:\/$|\/document\/(?:list|dept|site)$|\/document\/detail\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$)/.test(url);
  const validDocument = validUrl && url.includes('/document/detail/');
  const validFilename = !!filename.trim() && filename.length <= 300 && !/[\\/:\r\n<>"|?*]/.test(filename);
  const validOutput = output.length <= 500 && /^(?:[A-Za-z]:[\\/]|\/|\\\\)/.test(output) && !/[\r\n]/.test(output);
  const button = (label, action, disabled=false, extra={}) => jsx('button', {
    type:'button', disabled, 'data-dms-action':extra.menu?`menu-${extra.menu}`:action,
    className:'px-2 py-1 border rounded text-sm disabled:opacity-40',
    style:{borderColor:'var(--ui-stroke-secondary)'},
    onClick:()=>submit(`Nạp skill dms-fast:reading rồi dùng dms_fast_session với ${JSON.stringify({action:action==='open'||action==='search'?'prepare':action, work_id:work, ...(action==='open'?{task:{kind:'read',action:'open',url}}:action==='search'?{task:{kind:'search',query}}:{}), ...extra})}. Giữ Chrome; chờ tôi đăng nhập nếu cần. Menu chỉ xem, không đặt lịch hoặc tải hướng dẫn. Đây là đọc/search/trạng thái, không cấp quyền transfer. Tải mới phải chọn một tệp và dùng computer_use sau fresh read completed; không tạo plugin download task. Không hủy việc lạ, reset attempts/quota hoặc retry khi chưa rõ.`), children:label
  });
  return jsx('div', {className:'p-3 space-y-2', children:[
    jsx('strong',{children:'DMS Fast'}),
    jsx('p',{className:'text-xs',style:{color:'var(--ui-text-secondary)'},children:'Nhấn thao tác để gửi ngay tới phiên chat đang mở, không cần Gửi thêm. Không tự đăng nhập. Xác nhận Run phụ thuộc trust MCP do operator cấp.'}),
    jsx('button',{type:'button',className:'px-2 py-1 border rounded text-sm',onClick:()=>draft('Nạp skill dms-fast:reading. Đọc/search/metadata DMS chỉ qua dms_fast_session; tải mới một tệp đã chọn qua computer_use sau completed source verification và handoff. Không thao tác browser nếu chưa có quyền.'),children:'Nạp skill đọc DMS'}),
    jsx('input',{type:'text',value:work,onChange:e=>setWork(e.target.value),placeholder:'Work ID (chữ/số/gạch nối)', 'aria-label':'DMS work ID',className:'w-full border rounded p-1',style:{borderColor:'var(--ui-stroke-secondary)'}}),
    jsx('input',{type:'text',value:query,onChange:e=>setQuery(e.target.value),placeholder:'Từ khóa tìm nguồn', 'aria-label':'DMS search query',className:'w-full border rounded p-1',style:{borderColor:'var(--ui-stroke-secondary)'}}),
    jsx('input',{type:'text',value:url,onChange:e=>setUrl(e.target.value),placeholder:'Canonical DMS URL, không token/query', 'aria-label':'DMS canonical source URL',className:'w-full border rounded p-1',style:{borderColor:'var(--ui-stroke-secondary)'}}),
    button('Tìm nguồn','search',!validWork||!query.trim()||query.length>120),
    button('Mở đúng nguồn','open',!validWork||!validUrl),
    jsx('input',{type:'text',value:filename,onChange:e=>setFilename(e.target.value),placeholder:'Đúng tên một tệp đã chọn trên DMS','aria-label':'DMS selected download filename',className:'w-full border rounded p-1'}),
    jsx('input',{type:'text',value:output,onChange:e=>setOutput(e.target.value),placeholder:'Thư mục bàn giao absolute đã duyệt','aria-label':'DMS approved output directory',className:'w-full border rounded p-1'}),
    jsx('button',{type:'button','data-dms-action':'cua-download',disabled:!validWork||!validDocument||!validFilename||!validOutput,className:'px-2 py-1 border rounded text-sm disabled:opacity-40',
      onClick:()=>submit(`Tôi yêu cầu tải mới đúng MỘT tệp theo lựa chọn ${JSON.stringify({work_id:work,url,expected_file_name:filename,output_dir:output})}. Nạp dms-fast:reading, computer-use và reference computer-use-download.md. Đọc lại nguồn bằng dms_fast_session kind=read; chỉ handoff khi completed và URL/title/code/revision/hiệu lực được kiểm theo skill. Kiểm status nếu có việc cũ chưa rõ; không cancel/reset/replay hoặc đổi controller sau refusal. Kiểm bản local đã có để tránh tải lại. Dừng plugin controller trước computer_use trên đúng Chrome hiện có. Capture mới để đối chiếu đúng hàng có Download; filename/preview không thay export. Lưu baseline và ledger versioned; ghi attempt_uncertain TRƯỚC inner click, tối đa một click. Giữ approval/mode mặc định, không tự foreground. File phải ổn định, hết partial, kiểm format/cấu trúc và SHA256; copy nguyên bản không ghi đè, kiểm hash bản bàn giao và receipt local riêng. Không viết receipt CUA giả vào state plugin, không nạp Cognee, không báo toàn văn đã đọc.`),children:'Tải một tệp — Computer Use'}),
    button('Đọc giao diện đang mở','inspect',!validWork),
    ...[['internal','Văn bản nội bộ'],['departments','Phòng ban'],['sites','Công trình'],['charts','Dạng biểu đồ/hình ảnh'],['grid','Danh sách lưới'],['booking','Xem lịch họp/xe'],['guides','Xem hướng dẫn — đích cần kiểm']].map(([menu,label])=>button(label,'inspect',!validWork,{menu})),
    button('Khả năng và giới hạn','capabilities',!validWork),
    button('Trạng thái, không gọi Chrome','status',!validWork),
    button('Tiếp tục việc đang chờ','resume',!validWork),
    button('Hủy work quen thuộc — cần duyệt','cancel',!validWork),
    jsx('p',{className:'text-xs',style:{color:'var(--ui-text-secondary)'},children:'Quota: tối đa 5 văn bản/ngày; số lượt còn lại chưa biết. Kiểm tệp/hash/nguồn trước bàn giao. Metadata ≠ toàn văn; không lưu đăng nhập, không API ẩn.'})
  ]});
}

export default {
  id:'dms-fast-panel', name:'DMS Fast 0.6.0 — đọc DevTools, tải Computer Use',
  register(ctx) {
    ctx.register({id:'reader',area:'panes',title:'DMS Fast',data:{placement:'right',width:'310px'},render:()=>jsx(Panel,{})});
  }
};
