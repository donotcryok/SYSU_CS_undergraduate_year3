/**
 * @Copyright(C) 2008 Software Engineering Laboratory (SELAB), Department of Computer
 * Science, SUN YAT-SEN UNIVERSITY. All rights reserved.
 **/

package gui;

import parser.Calculator;

import javax.swing.*;
import javax.swing.border.Border;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.text.DecimalFormat;

/**
 * ExprEval 表达式计算器的主窗口。
 * <p>
 * 提供表达式输入、计算、清除、剪切/复制/粘贴、帮助和退出等完整的 GUI 功能。
 * 计算逻辑通过 {@link parser.Calculator} 完成，异常信息会直接显示在输出框中。
 * </p>
 *
 * @author 马福泉
 * @version 1.0
 */
public class MainWindow extends JFrame
{
	private static final long serialVersionUID = 1L;

	/** 输入框字符宽度 */
	private final int INPUT_FIELD_LENGTH = 30;

	/** 表达式输入文本框 */
	private JTextField inputField;

	/** 结果 / 异常输出文本框 */
	private JTextField outputField;

	/** "计算" 按钮 */
	private JButton calButton;

	/** 当前窗口引用，供帮助对话框定位 */
	private JFrame currentFrame;

	/**
	 * 构造主窗口，完成所有 GUI 组件的布局与事件绑定。
	 */
	public MainWindow()
	{
		// ---------- 窗口基本设置 ----------
		setTitle("ExprEval - An Expression Based Calculator");
		getContentPane().setLayout(new BorderLayout());
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

		// ---------- 中央面板：输入框 + 输出框 ----------
		JPanel centerPanel = new JPanel();
		getContentPane().add(centerPanel);
		centerPanel.setLayout(new GridLayout(2, 1, 10, 10));
		centerPanel.setBorder(BorderFactory.createEmptyBorder(8, 10, 8, 10));

		// --- 输入框 ---
		inputField = new JTextField(INPUT_FIELD_LENGTH);
		centerPanel.add(inputField);
		inputField.setBorder(BorderFactory.createLoweredBevelBorder());
		// 【修复】使用 "Dialog" 替代 "Arial" 以支持中文显示
		inputField.setFont(new Font("Dialog", Font.BOLD, 24));
		// 回车键触发计算
		inputField.addKeyListener(new KeyAdapter()
		{
			public void keyPressed(KeyEvent e)
			{
				if (e.getKeyChar() == '\n')
				{
					calButton.doClick();
				}
			}
		});

		// --- 输出框（只读，显示计算结果或异常信息）---
		outputField = new JTextField(INPUT_FIELD_LENGTH);
		centerPanel.add(outputField);
		// 【修复】使用 "Dialog" 替代 "Arial" 以支持中文显示
		outputField.setFont(new Font("Dialog", Font.BOLD, 24));
		outputField.setEnabled(false);

		// ---------- 底部工具栏：功能按钮 ----------
		JToolBar toolBar = new JToolBar();
		getContentPane().add(toolBar, BorderLayout.SOUTH);
		toolBar.setLayout(new GridLayout(1, 7, 8, 8));
		toolBar.setBorder(BorderFactory.createEmptyBorder(8, 10, 8, 10));

		// --- Calculate 按钮 ---
		calButton = new JButton("Calculate");
		toolBar.add(calButton);
		calButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				Calculator calculator = new Calculator();
				try
				{
					double result = calculator.calculate(inputField.getText());
					DecimalFormat df = new DecimalFormat("###,###,###,###.####");
					outputField.setText(df.format(result));
				}
				catch (Exception ex)
				{
					outputField.setText(ex.getMessage());
				}
			}
		});

		// --- Clear 按钮 ---
		JButton clearButton = new JButton("Clear");
		toolBar.add(clearButton);
		clearButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				inputField.setText("");
				outputField.setText("");
			}
		});

		// --- Cut 按钮 ---
		JButton cutButton = new JButton("Cut");
		toolBar.add(cutButton);
		cutButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				inputField.selectAll();
				inputField.cut();
			}
		});

		// --- Copy 按钮 ---
		JButton copyButton = new JButton("Copy");
		toolBar.add(copyButton);
		copyButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				outputField.setEnabled(true);
				outputField.selectAll();
				outputField.copy();
				outputField.setEnabled(false);
			}
		});

		// --- Paste 按钮 ---
		JButton pasteButton = new JButton("Paste");
		toolBar.add(pasteButton);
		pasteButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				inputField.setText("");
				inputField.paste();
			}
		});

		// --- Help 按钮 ---
		JButton helpButton = new JButton("Help");
		toolBar.add(helpButton);
		currentFrame = this;
		helpButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				JOptionPane.showMessageDialog(currentFrame, getHelpMessage());
			}
		});

		// --- Exit 按钮 ---
		JButton exitButton = new JButton("Exit");
		toolBar.add(exitButton);
		exitButton.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				System.exit(0);
			}
		});

		// ---------- 窗口收尾 ----------
		pack();
		setVisible(true);
	}

	/**
	 * 返回帮助信息文本，包含版权、版本及支持的表达式语法说明。
	 *
	 * @return 格式化的帮助字符串
	 */
	private String getHelpMessage()
	{
		String msg = "";
		msg = "ExprEval - An Expression Based Calculator, Version 1.0A\n"
			+ "Copyright(C) 2008, Dr. Wen-jun LI (SELAB), "
			+ "Department of Computer Science, SUN YAT-SEN UNIVERSITY. \n"
			+ "The experimental framework and reference solution are "
			+ "developed by Dr. Wen-jun LI and Da LUO. \n\n"
			+ "The fundamental version of ExprEval covers the following features: \n"
			+ "  1) Unsigned integral constants, for example \"058\" and \"123\". \n"
			+ "  2) Unsigned real constants, including scientific notation: "
			+ "\"3.14\", \"5.1E-5\", and \"101.25E+3\". \n"
			+ "  3) Binary arithmetic operations, for example "
			+ "\"1 + 2\", \"3 - 4\", \"5 * 6\", and \"7 / 8\". \n"
			+ "  4) Only one unary arithmetic operation, for example \"-100\". \n\n"
			+ "This version of ExprEval also features in: \n"
			+ "  a) Exponential operation, for example \"5 ^ 3\". \n"
			+ "  b) Boolean constants: \"true\" and \"false\". \n"
			+ "  c) Relational operations: \"=\", \"<>\", \"<\", \"<=\", \">\", and \">=\". \n"
			+ "  d) Logical operations: \"!\" (not), \"&\" (and), and \"|\" (or). \n"
			+ "  e) The only trinary operation, for example "
			+ "\"(12 * 2 > 20) ? 25 : 33\". \n"
			+ "  f) Predefined functions \"max(x1, x2, ...)\" and \"min(x1, x2, ...)\". \n"
			+ "  g) Predefined functions \"sin(x)\" and \"cos(x)\". \n";
		return msg;
	}
}
