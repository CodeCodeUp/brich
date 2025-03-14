from manim import *
import numpy as np

class BendingRectangleWithSplitColors(Scene):
    def construct(self):

        self.camera.frame_width = 7
        self.camera.frame_height = 6
        self.camera.background_color = WHITE

        w = 4
        h = 0.1
        h_top = 0.7 * h
        h_bottom = 0.2 * h
        w2 = 1
        h2 = 2
        gap = 1
        a_max = 0.3
        n_points_per_side = 20
        support_size = 0.5
        support_size_2 = 1

        def generate_rectangle_points(height, y_offset=0):
            points = []
            for i in range(n_points_per_side):
                x = -w / 2 + i * (w / (n_points_per_side - 1))
                points.append([x, -height / 2 + y_offset, 0])
            for i in range(1, n_points_per_side):
                y = -height / 2 + i * (height / (n_points_per_side - 1)) + y_offset
                points.append([w / 2, y, 0])
            for i in range(1, n_points_per_side):
                x = w / 2 - i * (w / (n_points_per_side - 1))
                points.append([x, height / 2 + y_offset, 0])
            for i in range(1, n_points_per_side - 1):
                y = height / 2- i * (height / (n_points_per_side - 1)) + y_offset
                points.append([-w / 2, y, 0])
            return points



        points_top = generate_rectangle_points(h_top, y_offset=h_bottom / 2)
        points_bottom = generate_rectangle_points(h_bottom, y_offset=-h_top / 2)

        rect_top = Polygon(*points_top).set_fill(RED_A, opacity=1).set_stroke(width=0)
        rect_bottom = Polygon(*points_bottom).set_fill(GREEN, opacity=1).set_stroke(width=0)

        # 初始位置，将矩形移动到左侧
        initial_x_offset = -self.camera.frame_width / 2 - w / 2
        rect_top.move_to([initial_x_offset, rect_top.get_center()[1], 0])
        rect_bottom.move_to([initial_x_offset, rect_bottom.get_center()[1], 0])

        image = ImageMobject("my2.png")
        image.stretch_to_fit_width(w2).stretch_to_fit_height(h2)
        image.move_to([0, h2/2 + gap - 0.15 , 0])

        support_left = Square(side_length=support_size_2).set_fill(GRAY, opacity=1).set_stroke(width=0)
        support_right = Square(side_length=support_size_2).set_fill(GRAY, opacity=1).set_stroke(width=0)
        support_left.move_to([-w/3 + 0.5, -h/2 - support_size_2/2, 0])
        support_right.move_to([w/3 - 0.5, -h/2 - support_size_2/2, 0])

        self.add(rect_top, rect_bottom, image, support_left, support_right)

        # rect_bottom 先移动到当前位置
        self.play(
            rect_bottom.animate.move_to([0, rect_bottom.get_center()[1], 0]),
            run_time=2
        )

        # rect_top 再移动到当前位置
        self.play(
            rect_top.animate.move_to([0, rect_top.get_center()[1], 0]),
            run_time=2
        )

        contact_y = h/2 + h2/2
        self.play(image.animate.move_to([0, contact_y - 0.15, 0]), run_time=2)

        def bend_function(a):
            theta_max = 1  # 增大最大旋转角度从0.3改为0.6
            left_pivot = np.array([-w/5 + support_size, 0, 0])
            right_pivot = np.array([w/5 - support_size, 0, 0])
            def func(p):
                x, y, z = p
                if -w/5 + support_size <= x <= w/5 - support_size:
                    bend = -a * (1 - ((x / (w/5 - support_size))**2))
                    return [x, y + bend, z]
                elif x < -w/5 + support_size:
                    theta = -(a / a_max) * theta_max  # 应用新的theta_max
                    p_vec = np.array([x, y, z]) - left_pivot
                    cos_theta = np.cos(theta)
                    sin_theta = np.sin(theta)
                    new_vec = np.array([
                        p_vec[0]*cos_theta - p_vec[1]*sin_theta,
                        p_vec[0]*sin_theta + p_vec[1]*cos_theta,
                        0
                    ])
                    return (left_pivot + new_vec).tolist()
                else:
                    theta = (a / a_max) * theta_max  # 应用新的theta_max
                    p_vec = np.array([x, y, z]) - right_pivot
                    cos_theta = np.cos(theta)
                    sin_theta = np.sin(theta)
                    new_vec = np.array([
                        p_vec[0]*cos_theta - p_vec[1]*sin_theta,
                        p_vec[0]*sin_theta + p_vec[1]*cos_theta,
                        0
                    ])
                    return (right_pivot + new_vec).tolist()
            return func

        def bend_function_buttom(a):
            theta_max = 1  # 增大最大旋转角度从0.3改为0.6
            left_pivot = np.array([-w/5 + support_size, 0, 0])
            right_pivot = np.array([w/5 - support_size, 0, 0])
            def func(p):
                x, y, z = p
                if -w/5 + support_size <= x <= w/5 - support_size:
                    bend = -a * (1 - ((x / (w/5 - support_size))**2))
                    return [x, y + bend, z]
                elif x < -w/5 + support_size:
                    theta = -(a / a_max) * theta_max  # 应用新的theta_max
                    p_vec = np.array([x, y, z]) - left_pivot
                    cos_theta = np.cos(theta)
                    sin_theta = np.sin(theta)
                    new_vec = np.array([
                        p_vec[0]*cos_theta - p_vec[1]*sin_theta,
                        p_vec[0]*sin_theta + p_vec[1]*cos_theta,
                        0
                    ])
                    return (left_pivot + new_vec).tolist()
                else:
                    theta = (a / a_max) * theta_max  # 应用新的theta_max
                    p_vec = np.array([x, y, z]) - right_pivot
                    cos_theta = np.cos(theta)
                    sin_theta = np.sin(theta)
                    new_vec = np.array([
                        p_vec[0]*cos_theta - p_vec[1]*sin_theta,
                        p_vec[0]*sin_theta + p_vec[1]*cos_theta,
                        0
                    ])
                    return (right_pivot + new_vec).tolist()
            return func

        a_tracker = ValueTracker(0)

        def update_rect_top(rect):
            a = a_tracker.get_value()
            rect.become(
                Polygon(*[bend_function(a)(p) for p in points_top])
                .set_fill(RED_A, opacity=1)
                .set_stroke(width=0)
            )

        def update_rect_bottom(rect):
            a = a_tracker.get_value()
            rect.become(
                Polygon(*[bend_function_buttom(a)(p) for p in points_bottom])
                .set_fill(GREEN, opacity=1)
                .set_stroke(width=0)
            )

        def update_image(img):
            a = a_tracker.get_value()
            top_y = h/4 - a
            img.move_to([0, top_y + h2/2 - 0.15, 0])

        rect_top.add_updater(update_rect_top)
        rect_bottom.add_updater(update_rect_bottom)
        image.add_updater(update_image)

        self.play(a_tracker.animate.set_value(a_max), run_time=2)

        rect_top.remove_updater(update_rect_top)
        rect_bottom.remove_updater(update_rect_bottom)
        image.remove_updater(update_image)

        self.wait(1)
