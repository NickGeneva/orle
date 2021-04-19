// Gmsh project created on Sun Aug 23 20:19:59 2020
// Export to .msh version 2 ascii
// Then use gmshToFoam cylinder_mesh.msh -case ./base_files
SetFactory("OpenCASCADE");

cp = 40;
sp = 2;
sw = 0.02;
r = 1.0;
r2 = 2.0;
sres = 25; //Sensor area
outres  = 25; //Outer area

//+
Point(1) = {0, 0, 0, 1.0};
//+
// Create cylinder
Point(2) = {r, 0.0, 0, 1.0};
//+
Point(3) = {r*Cos(Pi/4 - sw/r), r*Sin(Pi/4 - sw/r), 0, 1.0};
//+
Point(4) = {r*Cos(Pi/4 + sw/r), r*Sin(Pi/4 + sw/r), 0, 1.0};
//+
Point(5) = {0.0, 1.0, 0, 1.0};
//+
Point(6) = {r*Cos(3*Pi/4 - sw/r), r*Sin(3*Pi/4 - sw/r), 0, 1.0};
//+
Point(7) = {r*Cos(3*Pi/4 + sw/r), r*Sin(3*Pi/4 + sw/r), 0, 1.0};
//+
Point(8) = {-1.0, 0.0, 0, 1.0};
//+
Point(9) = {r*Cos(5*Pi/4 - sw/r), r*Sin(5*Pi/4 - sw/r), 0, 1.0};
//+
Point(10) = {r*Cos(5*Pi/4 + sw/r), r*Sin(5*Pi/4 + sw/r), 0, 1.0};
//+
Point(11) = {0.0, -1.0, 0, 1.0};
//+
Point(12) = {r*Cos(7*Pi/4 - sw/r), r*Sin(7*Pi/4 - sw/r), 0, 1.0};
//+
Point(13) = {r*Cos(7*Pi/4 + sw/r), r*Sin(7*Pi/4 + sw/r), 0, 1.0};
//+
Circle(1) = {2, 1, 3};
//+
Circle(2) = {3, 1, 4};
//+
Circle(3) = {4, 1, 5};
//+
Circle(4) = {5, 1, 6};
//+
Circle(5) = {6, 1, 7};
//+
Circle(6) = {7, 1, 8};
//+
Circle(7) = {8, 1, 9};
//+
Circle(8) = {9, 1, 10};
//+
Circle(9) = {10, 1, 11};
//+
Circle(10) = {11, 1, 12};
//+
Circle(11) = {12, 1, 13};
//+
Circle(12) = {13, 1, 2};

// Number of points on curves, should be even for jets to be placed on 45s
Transfinite Curve {1, 3, 4, 6, 7, 9, 10, 12} = cp/2 Using Progression 1.0;

Transfinite Curve {2, 5, 8, 11} = sp Using Progression 1.0;

// Outer cylinder
Point(14) = {r2, 0.0, 0, 1.0};
//+
Point(15) = {r2*Cos(Pi/4 - sw/r2), r2*Sin(Pi/4 - sw/r2), 0, 1.0};
//+
Point(16) = {r2*Cos(Pi/4 + sw/r2), r2*Sin(Pi/4 + sw/r2), 0, 1.0};
//+
Point(17) = {0.0, r2, 0, 1.0};
//+
Point(18) = {r2*Cos(3*Pi/4 - sw/r2), r2*Sin(3*Pi/4 - sw/r2), 0, 1.0};
//+
Point(19) = {r2*Cos(3*Pi/4 + sw/r2), r2*Sin(3*Pi/4 + sw/r2), 0, 1.0};
//+
Point(20) = {-r2, 0.0, 0, 1.0};
//+
Point(21) = {r2*Cos(5*Pi/4 - sw/r2), r2*Sin(5*Pi/4 - sw/r2), 0, 1.0};
//+
Point(22) = {r2*Cos(5*Pi/4 + sw/r2), r2*Sin(5*Pi/4 + sw/r2), 0, 1.0};
//+
Point(23) = {0.0, -r2, 0, 1.0};
//+
Point(24) = {r2*Cos(7*Pi/4 - sw/r2), r2*Sin(7*Pi/4 - sw/r2), 0, 1.0};
//+
Point(25) = {r2*Cos(7*Pi/4 + sw/r2), r2*Sin(7*Pi/4 + sw/r2), 0, 1.0};
//+
Circle(13) = {14, 1, 15};
//+
Circle(14) = {15, 1, 16};
//+
Circle(15) = {16, 1, 17};
//+
Circle(16) = {17, 1, 18};
//+
Circle(17) = {18, 1, 19};
//+
Circle(18) = {19, 1, 20};
//+
Circle(19) = {20, 1, 21};
//+
Circle(20) = {21, 1, 22};
//+
Circle(21) = {22, 1, 23};
//+
Circle(22) = {23, 1, 24};
//+
Circle(23) = {24, 1, 25};
//+
Circle(24) = {25, 1, 14};

// Number of points on curves, should be even for jets to be placed on 45s
Transfinite Curve {13, 15, 16, 18, 19, 21, 22, 24} = cp/2 Using Progression 1.0;

Transfinite Curve {14, 17, 20, 23} = sp Using Progression 1.0;

//+
Line(25) = {2, 14};
//+
Line(26) = {3, 15};
//+
Line(27) = {4, 16};
//+
Line(28) = {5, 17};
//+
Line(29) = {6, 18};
//+
Line(30) = {7, 19};
//+
Line(31) = {8, 20};
//+
Line(32) = {9, 21};
//+
Line(33) = {10, 22};
//+
Line(34) = {11, 23};
//+
Line(35) = {12, 24};
//+
Line(36) = {13, 25};

Transfinite Curve {25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36} = cp/2 Using Progression 1.05;//+
Curve Loop(1) = {1, 26, -13, -25};
//+
Plane Surface(1) = {1};
//+
Curve Loop(2) = {2, 27, -14, -26};
//+
Plane Surface(2) = {2};
//+
Curve Loop(3) = {3, 28, -15, -27};
//+
Plane Surface(3) = {3};
//+
Curve Loop(4) = {4, 29, -16, -28};
//+
Plane Surface(4) = {4};
//+
Curve Loop(5) = {5, 30, -17, -29};
//+
Plane Surface(5) = {5};
//+
Curve Loop(6) = {6, 31, -18, -30};
//+
Plane Surface(6) = {6};
//+
Curve Loop(7) = {7, 32, -19, -31};
//+
Plane Surface(7) = {7};
//+
Curve Loop(8) = {8, 33, -20, -32};
//+
Plane Surface(8) = {8};
//+
Curve Loop(9) = {9, 34, -21, -33};
//+
Plane Surface(9) = {9};
//+
Curve Loop(10) = {10, 35, -22, -34};
//+
Plane Surface(10) = {10};
//+
Curve Loop(11) = {11, 36, -23, -35};
//+
Plane Surface(11) = {11};
//+
Curve Loop(12) = {12, 25, -24, -36};
//+
Plane Surface(12) = {12};

Transfinite Surface {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};
//+
Recombine Surface {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

// Sensor Region
Point(50) = {3, 3, 0, 1.0};
//+
Point(51) = {6, 3, 0, 1.0};
//+
Point(52) = {3, -3, 0, 1.0};
//+
Point(53) = {6, -3, 0, 1.0};
//+
Line(97) = {50, 51};
//+
Line(98) = {51, 53};
//+
Line(99) = {53, 52};
//+
Line(100) = {52, 50};
//+
Transfinite Curve {98, 100} = 2*sres Using Progression 1.0;//+
//+
Transfinite Curve {97, 99} = sres Using Progression 1.0;//+
//+
Curve Loop(61) = {100, 97, 98, 99};
//+
Plane Surface(61) = {61};
// +
Transfinite Surface {61};
//+
Recombine Surface {61};

// Box around cylinder
Point(58) = {-3, 3, 0, 1.0};
//+
Point(59) = {-3, -3, 0, 1.0};
//+
Line(109) = {50, 58};
//+
Line(110) = {58, 59};
//+
Line(111) = {59, 52};
//+
Transfinite Curve {109, 110, 111} = sres/2 Using Progression 1.0;//+
//+
Curve Loop(67) = {22, 23, 24, 13, 14, 15, 16, 17, 18, 19, 20, 21};
//+
Curve Loop(68) = {111, 100, 109, 110};
//+
Plane Surface(68) = {68, 67};

// Outer box
Point(76) = {-5, 5, 0, 1.0};
//+
Point(77) = {-5, -5, 0, 1.0};
//+
Point(78) = {30, -5, 0, 1.0};
//+
Point(79) = {30, 5, 0.0, 1.0};
//+
Line(144) = {76, 79};
//+
Line(145) = {79, 78};
//+
Line(146) = {78, 77};
//+
Line(147) = {77, 76};
//+
Transfinite Curve {144, 146} = 3*outres Using Progression 1.0; 
Transfinite Curve {145, 147} = outres Using Progression 1.0;
//+
Curve Loop(87) = {111, -99, -98, -97, 109, 110};
//+
Curve Loop(88) = {146, 147, 144, 145};
//+
Plane Surface(87) = {88, 87};


Extrude {0, 0, 0.1} {
  Surface{10}; Surface{11}; Surface{12}; Surface{1}; Surface{2}; Surface{4}; Surface{5}; Surface{6}; Surface{7}; Surface{8}; Surface{9}; Surface{68}; Surface{61}; Surface{87}; Surface{3}; 
  Layers {1}; 
  Recombine;
}
//+
Physical Surface("inlet", 229) = {144};
//+
Physical Surface("wall", 230) = {145, 143};
//+
Physical Surface("outlet", 231) = {146};
//+
Physical Surface("cylinder", 232) = {101, 148, 109, 118, 122, 130, 88, 97};
//+
Physical Surface("jet1", 233) = {114};
//+
Physical Surface("jet2", 234) = {105};
//+
Physical Surface("jet3", 235) = {93};
//+
Physical Surface("jet4", 236) = {126};
//+
Physical Surface("cyclic1", 237) = {87, 61, 68, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11};
//+
Physical Surface("cyclic2", 238) = {147, 138, 121, 117, 113, 149, 108, 104, 100, 96, 92, 132, 129, 125, 142};
//+
Physical Volume("Volume", 239) = {14, 13, 12, 3, 2, 11, 9, 8, 7, 6, 15, 5, 4, 10, 1};