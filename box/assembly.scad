explode = 0.01;
opacity = 0.5;
show_door = true;
show_box = true;
show_battery = false;
show_stereopi = true;
simplified_stereopi = true;

module bottom() {
    linear_extrude(height = 3)
        import("exported_parts/p_bottom.dxf");
}

module sideL() {
    rotate([90, 0, -90])
        linear_extrude(height = 3)
            import("exported_parts/p_side.dxf");
}

module sideR() {
    rotate([90, 0, -90])
        translate([0, 0, -3])
            linear_extrude(height = 3)
                import("exported_parts/p_side.dxf");
}

module front() {
    rotate([90, 0, 0])
        linear_extrude(height = 3)
            import("exported_parts/p_front.dxf");
}

module backT() {
    rotate([90, 0, 0])
        translate([0, 0, -3])
            linear_extrude(height = 3)
                import("exported_parts/p_back.dxf");
}

module backB() {
    rotate([-90, 0, 0])
        linear_extrude(height = 3)
            import("exported_parts/p_back.dxf");
}

module top() {
    translate([0, 0, -3])
        linear_extrude(height = 3)
            import("exported_parts/p_top.dxf");
}

module door() {
    rotate([90, 0, 0])
        translate([0, 0, -3])
            linear_extrude(height = 3)
                import("exported_parts/p_door.dxf");
}

module caps() {
    linear_extrude(height = 3)
        import("exported_parts/p_caps.dxf");
}

module tongue() {
    linear_extrude(height = 3)
        import("exported_parts/p_tongue.dxf");
}

module screen_bottomL() {
    rotate([90, 0, 90])
        linear_extrude(height = 3)
            import("exported_parts/p_screen_bottom.dxf");
}

module screen_bottomR() {
    rotate([90, 0, 90])
        translate([0, 0, -3])
            linear_extrude(height = 3)
                import("exported_parts/p_screen_bottom.dxf");
}

module screen_top() {
    linear_extrude(height = 3)
        import("exported_parts/p_screen_top.dxf");
}

module stpiholder() {
    rotate([90, 0, 0])
        linear_extrude(height = 3)
            import("exported_parts/p_stpiholder.dxf");
}

module assembly() {
    if (show_box) {
        translate([0, 0, -explode]) bottom();
        translate([60 + explode, 0, 0]) sideL();
        translate([-60 - explode, 0, 0]) sideR();
        translate([0, 26 + explode, 120]) backT();
        translate([0, 26 + explode, 43]) backB();
        translate([0, 0, 160 + explode]) top();
    }
    translate([0, -26 - explode, 0]) front();
    translate([0, -25, 136]) caps();
    translate([0, -26, 90]) tongue();
    translate([28.5, -29, 0]) screen_bottomL();
    translate([-28.5, -29, 0]) screen_bottomR();
    translate([0, -18 + explode, 41]) screen_top();
    translate([0, 11 + explode, 62]) stpiholder();
    if (show_door)
        translate([0, 23, 30 * explode]) door();
}

module stereopi() {
    translate([-6.5, -8.9, 85.9]) {
        rotate([90, 180, 0]) {
            translate([-45, -21.6, -11.39])
                cube([90, 40, 1.2]);
            translate([-36, -21.6, -17.5])
                color("red") cube([72,36.1,7]);
            if (simplified_stereopi) {
                translate([-14, -21.6, -10])
                    cube([34,21,15.7]);
            } else {
                import("/tmp/sp.stl"); // Requieres the STL stereopi model to display it.
            }
            translate([32.5, 10.85, 17.1]) {
                rotate([0, 180, 0]) {
                    union() {
                        cube([85,55,5.5]);
                        translate([7, 0, 5.5])
                            cube([33,6,18]);
                        translate([19,7,5.5])
                            color("red") cube([41,38,1.5]);
                        translate([1.5, 2,-0.1])
                            color("white") cube([75, 51, 0.1]);
                    }
                }
            }
        }
    }
}

module battery() {
    translate([0,0,160])
        cube([140, 75, 18], center=true);
}

%color([0.85, 0.79, 0.69, opacity])
    assembly();
if (show_battery) battery();
if (show_stereopi) stereopi();