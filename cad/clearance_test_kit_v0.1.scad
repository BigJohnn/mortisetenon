// Printable Joinery Atlas — Clearance Test Kit v0.1
// Unit: mm
// Definition: total clearance C = socket width - peg shank width.
// First-round values: 0.10 / 0.20 / 0.30 / 0.40 mm.

$fn = 48;
peg = 12.0;
clearances = [0.10, 0.20, 0.30, 0.40];
board_t = 5.0;
cell_w = 27;
board_margin = 5;
board_d = 30;
lead_in = 0.6;
peg_h = 10;
head_xy = 18;
head_h = 4;
peg_spacing_y = 24;

module socket(c){
  // main through socket
  translate([0,0,-0.1]) cube([peg+c, peg+c, board_t+0.2], center=false);
  // shallow larger top lead-in; square rather than decorative chamfer for predictable print
  translate([-lead_in/2,-lead_in/2,board_t-lead_in])
    cube([peg+c+lead_in, peg+c+lead_in, lead_in+0.2], center=false);
}

module test_board(){
  board_w = board_margin*2 + cell_w*len(clearances);
  difference(){
    cube([board_w, board_d, board_t]);
    for(i=[0:len(clearances)-1]){
      x = board_margin + i*cell_w + (cell_w-(peg+clearances[i]))/2;
      y = (board_d-(peg+clearances[i]))/2;
      translate([x,y,0]) socket(clearances[i]);
    }
  }
}

module peg_tool(){
  // head on bed, shank upward; insertion end is top.
  union(){
    cube([head_xy,head_xy,head_h]);
    translate([(head_xy-peg)/2,(head_xy-peg)/2,head_h]) cube([peg,peg,peg_h]);
  }
}

// Board + four loose pegs in one STL as disconnected shells.
test_board();
for(i=[0:len(clearances)-1]){
  translate([board_margin+i*(head_xy+6), board_d+peg_spacing_y, 0]) peg_tool();
}
